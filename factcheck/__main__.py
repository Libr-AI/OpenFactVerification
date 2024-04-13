import json
import time
import tiktoken
import argparse
import os

from factcheck.utils.LLMClient import ChatGPTClient
from factcheck.utils.prompt import BasePrompt, ChatGPTPrompt
from factcheck.utils.CustomLogger import CustomLogger
from factcheck.utils.multimodal import modal_normalization
from factcheck.config.load_config import load_yaml
from factcheck.core import (
    Decompose,
    Checkworthy,
    QueryGenerator,
    SerperEvidenceRetrieve,
    ClaimVerify,
)

logger = CustomLogger(__name__).getlog()


class FactCheck:
    def __init__(
        self,
        default_model: str = "gpt-4-0125-preview",
        prompt: str = "chatgpt_prompt",
        decompose_model: str = None,
        checkworthy_model: str = None,
        query_generator_model: str = None,
        evidence_retrieval_model: str = None,
        claim_verify_model: str = None,
        api_config: dict = None,
    ):
        self.encoding = tiktoken.get_encoding("cl100k_base")

        self.prompt = (
            ChatGPTPrompt() if prompt == "chatgpt_prompt" else BasePrompt()
        )  # TODO: better handling of prompt

        self.load_config(api_config=api_config)

        # llms for each step (sub-module)
        self.decompose_model = ChatGPTClient(
            model=default_model if decompose_model is None else decompose_model
        )
        self.checkworthy_model = ChatGPTClient(
            model=default_model if checkworthy_model is None else checkworthy_model
        )
        self.query_generator_model = ChatGPTClient(
            model=(
                default_model
                if query_generator_model is None
                else query_generator_model
            )
        )
        self.evidence_retrieval_model = evidence_retrieval_model  # no LLM for this step
        self.claim_verify_model = ChatGPTClient(
            model=default_model if claim_verify_model is None else claim_verify_model
        )

        # sub-modules
        self.decomposer = Decompose(llm_client=self.decompose_model, prompt=self.prompt)
        self.checkworthy = Checkworthy(
            llm_client=self.checkworthy_model, prompt=self.prompt
        )
        self.query_generator = QueryGenerator(
            llm_client=self.query_generator_model, prompt=self.prompt
        )
        self.evidence_crawler = SerperEvidenceRetrieve()
        self.claimverify = ClaimVerify(
            llm_client=self.claim_verify_model, prompt=self.prompt
        )

        logger.info("===Sub-modules Init Finished===")

    def load_config(self, api_config: dict) -> None:
        if api_config is None:
            api_config = dict()
        assert type(api_config) is dict, "api_config must be a dictionary."

        self.api_config = api_config

        # Load API keys from environment variables or config file, environment variables take precedence
        self.SERPER_API_KEY = os.environ.get(
            "SERPER_API_KEY", api_config.get("SERPER_API_KEY", None)
        )
        self.OPENAI_API_KEY = os.environ.get(
            "OPENAI_API_KEY", api_config.get("OPENAI_API_KEY", None)
        )
        self.ANTHROPIC_API_KEY = os.environ.get(
            "ANTHROPIC_API_KEY", api_config.get("ANTHROPIC_API_KEY", None)
        )
        self.LOCAL_API_KEY = os.environ.get(
            "LOCAL_API_KEY", api_config.get("LOCAL_API_KEY", None)
        )
        self.LOCAL_API_URL = os.environ.get(
            "LOCAL_API_URL", api_config.get("LOCAL_API_URL", None)
        )

    def check_response(self, response: str):
        st_time = time.time()
        # step 1
        claims = self.decomposer.getclaims(doc=response)
        for i, claim in enumerate(claims):
            logger.info(f"== response claims {i}: {claim}")

        # step 2
        (
            checkworthy_claims,
            pairwise_checkworthy,
        ) = self.checkworthy.identify_checkworthiness(claims)
        for i, claim in enumerate(checkworthy_claims):
            logger.info(f"== Check-worthy claims {i}: {claim}")

        # Token count
        num_raw_tokens = len(self.encoding.encode(response))
        num_checkworthy_tokens = len(self.encoding.encode(" ".join(checkworthy_claims)))

        api_data_dict = {
            "response": response,
            "token_count": {
                "num_raw_tokens": num_raw_tokens,
                "num_checkworthy_tokens": num_checkworthy_tokens,
            },
            "step_info": {
                "0_response": response,
                "1_decompose": claims,
                "2_checkworthy": checkworthy_claims,
                "2_checkworthy_pairwise": pairwise_checkworthy,
                "3_query_generator": {},
                "4_evidence_retrieve": {},
                "5_claim_verify": {},
            },
        }
        # Special case, return
        if num_checkworthy_tokens == 0:
            api_data_dict["factuality"] = "Nothing to check."
            logger.info("== State: Done! (Nothing to check.)")
            return api_data_dict

        # step 3
        claim_query_dict = self.query_generator.generate_query(
            claims=checkworthy_claims
        )
        for k, v in claim_query_dict.items():
            logger.info(f"== Claim: {k} --- Queries: {v}")

        step123_time = time.time()

        # step 4
        claim_evidence_dict = self.evidence_crawler.retrieve_evidence(
            claim_query_dict=claim_query_dict
        )
        for claim, evidences in claim_evidence_dict.items():
            logger.info(f"== Claim: {claim}")
            logger.info(f"== Evidence: {evidences}\n")
        step4_time = time.time()

        # step 5
        claim_verify_dict = self.claimverify.verify_claims(
            claims_evidences_dict=claim_evidence_dict
        )
        step5_time = time.time()
        logger.info(
            f"== State: Done! \n Total time: {step5_time-st_time:.2f}s. (create claims:{step123_time-st_time:.2f}s |||  retrieve:{step4_time-step123_time:.2f}s ||| verify:{step5_time-step4_time:.2f}s)"
        )

        api_data_dict["step_info"].update(
            {
                "3_query_generator": claim_query_dict,
                "4_evidence_retrieve": claim_evidence_dict,
                "5_claim_verify": claim_verify_dict,
            }
        )
        api_data_dict = self._post_process(api_data_dict, claim_verify_dict)
        api_data_dict["step_info"] = api_data_dict["step_info"]

        return api_data_dict

    def _post_process(self, api_data_dict, claim_verify_dict: dict):
        label_list = list()
        api_claim_data_list = list()
        for claim in api_data_dict["step_info"]["2_checkworthy"]:
            api_claim_data = {}
            claim_detail = claim_verify_dict.get(claim, {})
            curr_claim_label = claim_detail.get("factuality", False)
            label_list.append(curr_claim_label)
            api_claim_data["claim"] = claim
            api_claim_data["factuality"] = curr_claim_label
            api_claim_data["correction"] = claim_detail.get("correction", "")
            api_claim_data["reference_url"] = claim_detail.get("url", "")
            api_claim_data_list.append(api_claim_data)
        api_data_dict["factuality"] = all(label_list) if label_list else True
        api_data_dict["claims_details"] = api_claim_data_list
        return api_data_dict


def check(model: str, modal: str, input: str):
    """factcheck

    Args:
        model (str): gpt model used for factchecking
        modal (str): input type, supported types are str, text file, speech, image, and video
        input (str): input content or path to the file
    """
    factcheck = FactCheck(default_model=model)
    content = modal_normalization(modal, input)
    res = factcheck.check_response(content)
    print(json.dumps(res["step_info"], indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4-0125-preview")
    parser.add_argument("--modal", type=str, default="text")
    parser.add_argument("--input", type=str, default="demo_data/text.txt")
    parser.add_argument("--api_config", type=str, default="demo_data/api_config.yaml")
    args = parser.parse_args()

    print(args.model, args.modal, args.input, args.api_config)
    # check(args.model, args.modal, args.input)

    print(load_yaml(args.api_config))