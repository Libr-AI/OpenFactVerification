import concurrent.futures
import time
import tiktoken

from factcheck.utils.llmclient import CLIENTS, model2client
from factcheck.utils.prompt import prompt_mapper
from factcheck.utils.logger import CustomLogger
from factcheck.utils.api_config import load_api_config
from factcheck.core import (
    Decompose,
    Checkworthy,
    QueryGenerator,
    retriever_mapper,
    ClaimVerify,
)

logger = CustomLogger(__name__).getlog()


class FactCheck:
    def __init__(
        self,
        default_model: str = "gpt-4o",
        client: str = None,
        prompt: str = "chatgpt_prompt",
        retriever: str = "serper",
        decompose_model: str = None,
        checkworthy_model: str = None,
        query_generator_model: str = None,
        evidence_retrieval_model: str = None,
        claim_verify_model: str = None,  # "gpt-3.5-turbo",
        api_config: dict = None,
        num_seed_retries: int = 3,
    ):
        self.encoding = tiktoken.get_encoding("cl100k_base")

        self.prompt = prompt_mapper(prompt_name=prompt)

        # load configures for API
        self.load_config(api_config=api_config)

        # llms for each step (sub-module)
        step_models = {
            "decompose_model": decompose_model,
            "checkworthy_model": checkworthy_model,
            "query_generator_model": query_generator_model,
            "evidence_retrieval_model": evidence_retrieval_model,
            "claim_verify_model": claim_verify_model,
        }

        for key, _model_name in step_models.items():
            _model_name = default_model if _model_name is None else _model_name
            print(f"== Init {key} with model: {_model_name}")
            if client is not None:
                logger.info(f"== Use specified client: {client}")
                LLMClient = CLIENTS[client]
            else:
                logger.info("== LLMClient is not specified, use default llm client.")
                LLMClient = model2client(_model_name)
            setattr(self, key, LLMClient(model=_model_name, api_config=self.api_config))

        # sub-modules
        self.decomposer = Decompose(llm_client=self.decompose_model, prompt=self.prompt)
        self.checkworthy = Checkworthy(llm_client=self.checkworthy_model, prompt=self.prompt)
        self.query_generator = QueryGenerator(llm_client=self.query_generator_model, prompt=self.prompt)
        self.evidence_crawler = retriever_mapper(retriever_name=retriever)(api_config=self.api_config)
        self.claimverify = ClaimVerify(llm_client=self.claim_verify_model, prompt=self.prompt)
        self.num_seed_retries = num_seed_retries

        logger.info("===Sub-modules Init Finished===")

    def load_config(self, api_config: dict) -> None:
        # Load API config
        self.api_config = load_api_config(api_config)

    def check_response(self, response: str):
        st_time = time.time()
        # step 1
        claims = self.decomposer.getclaims(doc=response, num_retries=self.num_seed_retries)
        # Parallel run restore claims and checkworthy
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_claim2doc = executor.submit(
                self.decomposer.restore_claims, doc=response, claims=claims, num_retries=self.num_seed_retries
            )
            # step 2
            future_checkworthy_claims = executor.submit(
                self.checkworthy.identify_checkworthiness, claims, num_retries=self.num_seed_retries
            )
            # step 3
            future_claim_query_dict = executor.submit(self.query_generator.generate_query, claims=claims)

            # Wait for all futures to complete
            claim2doc = future_claim2doc.result()
            checkworthy_claims, pairwise_checkworthy = future_checkworthy_claims.result()
            claim_query_dict = future_claim_query_dict.result()

        checkworthy_claims_S = set(checkworthy_claims)
        claim_query_dict = {k: v for k, v in claim_query_dict.items() if k in checkworthy_claims_S}

        for i, (claim, origin) in enumerate(claim2doc.items()):
            logger.info(f"== response claims {i} --- {claim} --- {origin}")
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
                "1_restore": claim2doc,
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

        for k, v in claim_query_dict.items():
            logger.info(f"== Claim: {k} --- Queries: {v}")

        step123_time = time.time()

        # step 4
        claim_evidence_dict = self.evidence_crawler.retrieve_evidence(claim_query_dict=claim_query_dict)
        for claim, evidences in claim_evidence_dict.items():
            logger.info(f"== Claim: {claim}")
            logger.info(f"== Evidence: {evidences}\n")
        step4_time = time.time()

        # step 5
        claim_verify_dict = self.claimverify.verify_claims(claims_evidences_dict=claim_evidence_dict)
        for k, v in claim_verify_dict.items():
            logger.info(f"== Claim: {k} --- Verify: {v}")
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
        api_claim_data_list = []
        for claim, origin in api_data_dict["step_info"]["1_restore"].items():
            api_claim_data = {}
            api_claim_data["claim"] = claim
            api_claim_data["origin"] = origin
            if claim not in claim_verify_dict:
                api_claim_data["factuality"] = "Nothing to check."
            else:
                api_claim_data["evidence"] = claim_verify_dict.get(claim, {})
                labels = list(map(lambda x: x["relationship"], api_claim_data["evidence"]))
                if labels.count("SUPPORTS") + labels.count("REFUTES") == 0:
                    api_claim_data["factuality"] = 1  # "No evidence found."
                else:
                    api_claim_data["factuality"] = labels.count("SUPPORTS") / (
                        labels.count("REFUTES") + labels.count("SUPPORTS")
                    )
            api_claim_data_list.append(api_claim_data)
        api_data_dict["claim_details"] = api_claim_data_list

        valid_claims = list(filter(lambda x: not isinstance(x["factuality"], str), api_claim_data_list))
        api_data_dict["summary"] = {
            "num_claims": len(valid_claims),
            "overall_factuality": sum(map(lambda x: x["factuality"], valid_claims)) / len(valid_claims),
        }
        return api_data_dict
