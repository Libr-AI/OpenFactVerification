# coding:utf8
from __future__ import annotations

import time
import tiktoken

from factcheck.core.Decompose import Decompose
from factcheck.core.CheckWorthy import Checkworthy
from factcheck.core.QueryGenerator import QueryGenerator
from factcheck.core.Retriever import SerperEvidenceRetrieve
from factcheck.core.ClaimVerify import ClaimVerify

from factcheck.config.CustomLogger import CustomLogger

logger = CustomLogger(__name__).getlog()


class FactCheck:
    def __init__(
        self,
        default_model: str = "gpt-3.5-turbo-1106",
        decompose_model: str = None,
        checkworthy_model: str = None,
        query_generator_model: str = None,
        evidence_retrieval_model: str = None,
        claim_verify_model: str = None,
    ):
        # for gpt token count
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # claim getter
        self.decomposer = Decompose(
            model=default_model if decompose_model is None else decompose_model
        )
        # checkworthy
        self.checkworthy = Checkworthy(
            model=default_model if checkworthy_model is None else checkworthy_model
        )
        self.query_generator = QueryGenerator(
            model=(
                default_model
                if query_generator_model is None
                else query_generator_model
            )
        )
        # evidences crawler
        self.evidence_crawler = SerperEvidenceRetrieve(
            model=(
                default_model
                if evidence_retrieval_model is None
                else evidence_retrieval_model
            )
        )
        # verity claim with evidences
        self.claimverify = ClaimVerify(
            model=default_model if claim_verify_model is None else claim_verify_model
        )
        logger.info("===Sub-modules Init Finished===")

    def check_response(self, response: str):
        st_time = time.time()
        # step 1
        claims = self.decomposer.getclaimsfromgpt(doc=response)
        for i, claim in enumerate(claims):
            logger.info(f"== response claims {i}: {claim}")

        # step 2
        checkworthy_claims, pairwise_checkworthy = (
            self.checkworthy.identify_checkworthiness(claims)
        )
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
            },
        }
        # Special case, return
        if num_checkworthy_tokens == 0:
            api_data_dict["factuality"] = True
            logger.info(f"== State: Done! (Nothing to check.)")
            return api_data_dict

        # step 3
        claim_query_dict = self.query_generator.generate_query(claims=claims)
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
