from __future__ import annotations

import json
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class ClaimVerify:
    def __init__(self, llm_client, prompt):
        """Initialize the ClaimVerify class

        Args:
            llm_client (BaseClient): The LLM client used for verifying the factuality of claims.
            prompt (BasePrompt): The prompt used for verifying the factuality of claims.
        """
        self.llm_client = llm_client
        self.prompt = prompt

    def verify_claims(self, claims_evidences_dict, prompt: str = None) -> dict[str, any]:
        """Verify the factuality of the claims with respect to the given evidences

        Args:
            claims_evidences_dict (dict): a dictionary of claims and their corresponding evidences.

        Returns:
            dict: a dictionary of claims and their corresponding factuality results, including reasoning, error, correction, and factuality.
        """
        claim_detail_dict = dict()

        claims = list(claims_evidences_dict.keys())
        evidence_lists = list(claims_evidences_dict.values())
        results = self._verify_all_claims(claims, evidence_lists, prompt=prompt)

        for claim, evidence_list, result in zip(claims, evidence_lists, results):
            result["claim"] = claim
            result["evidence"] = evidence_list
            claim_detail_dict[claim] = result
        return claim_detail_dict

    def _verify_all_claims(
        self,
        claims: list[str],
        evidence_lists: list[list],
        num_retries=3,
        prompt: str = None,
    ) -> list[dict[str, any]]:
        """Verify the factuality of the claims with respect to the given evidences

        Args:
            claims (list[str]): a list of claims to verify.
            evidence_lists (list[list]): a list of evidences corresponding to the claims.
            num_retries (int, optional): maximum attempts for GPT to verify the factuality of the claims. Defaults to 3.

        Returns:
            list[dict[str, any]]: a list of factuality results, including reasoning, error, correction, and factuality.
        """
        factual_results = [None] * len(claims)
        attempts = 0
        # construct user inputs with respect to each claim and its evidences
        messages_list = []
        for claim, evidences in zip(claims, evidence_lists):
            if prompt is None:
                user_input = self.prompt.verify_prompt.format(claim=claim, evidence=evidences)
            else:
                user_input = prompt.format(claim=claim, evidence=evidences)

            messages_list.append(user_input)

        while (attempts < num_retries) and (None in factual_results):
            _messages = [_message for _i, _message in enumerate(messages_list) if factual_results[_i] is None]
            _indices = [_i for _i, _message in enumerate(messages_list) if factual_results[_i] is None]

            _message_list = self.llm_client.construct_message_list(_messages)
            _response_list = self.llm_client.multi_call(_message_list)
            for _response, _index in zip(_response_list, _indices):
                try:
                    _response_json = json.loads(_response)
                    assert all(k in _response_json for k in ["reasoning", "error", "correction", "factuality"])
                    factual_results[_index] = _response_json
                except:  # noqa: E722
                    logger.info(f"Warning: LLM response parse fail, retry {attempts}.")
            attempts += 1

        _template_results = {
            "reasoning": "[System Warning] Can not identify the factuality of the claim.",
            "error": "",
            "correction": "",
            "factuality": False,
        }
        # if cannot get correct response within num_retries times.
        factual_results = [_item if _item is not None else _template_results for _item in factual_results]
        return factual_results
