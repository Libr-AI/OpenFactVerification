from collections import Counter
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass


@dataclass
class TokenUsage:
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: Optional[int] = 0


@dataclass
class PipelineUsage:
    decomposer: TokenUsage = None
    checkworthy: TokenUsage = None
    query_generator: TokenUsage = None
    evidence_crawler: TokenUsage = None
    claimverify: TokenUsage = None


@dataclass
class Evidence:
    claim: str = None
    text: str = None  # evidence text
    url: str = None
    reasoning: str = None
    relationship: str = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False
        return True


@dataclass
class ClaimDetail:
    """Dataclass to store the details of a claim.

    Attributes:
        id (int): The unique identifier of the claim. [create from checkworthy]
        claim (str): The claim text. [create from checkworthy]
        checkworthy (bool): Whether the claim is checkworthy. [create from checkworthy]
        checkworthy_reason (str): The reason why the claim is checkworthy. [create from checkworthy]
        origin_text (str): The original text from which the claim was extracted. [create from decompose]
        start (int): The start index of the claim in the original text. [create from decompose]
        end (int): The end index of the claim in the original text. [create from decompose]
        queries (List[str]): The list of queries generated for the claim. [create from query_generator]
        evidences (List[Evidence]): The list of evidences retrieved for the claim. [createfrom evidence_crawler]
        factuality (any): The factuality of the claim. [create by summarize evidences]
            possible values: "Nothing to check.", "No evidence found", float in [0, 1]
    """

    id: int = None
    claim: str = None
    checkworthy: bool = None
    checkworthy_reason: str = None
    origin_text: str = None
    start: int = None
    end: int = None
    queries: List[str] = None
    evidences: List[dict] = None
    factuality: any = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False
        for evidence in self.evidences:
            if not evidence.attribute_check():
                print(f"Field {field.name} is None")
                return False
        return True


@dataclass
class FCSummary:
    """Dataclass to store the summary of the fact-checking process.

    Attributes:
        num_claims (int): The number of claims processed. [create from decompose]
        num_checkworthy_claims (int): The number of claims identified as checkworthy. [create from checkworthy]
        num_verified_claims (int): The number of claims that were verified. [create from claimverify - no evidence founded claims]
        num_supported_claims (int)
        num_refuted_claims (int)
        num_controversial_claims (int)
        factuality (float): The overall factuality.
    """

    num_claims: int = None
    num_checkworthy_claims: int = None
    num_verified_claims: int = None
    num_supported_claims: int = None
    num_refuted_claims: int = None
    num_controversial_claims: int = None
    factuality: float = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False
        return True


@dataclass
class FactCheckOutput:
    raw_text: str = None
    token_count: int = None
    usage: PipelineUsage = None
    claim_detail: List[ClaimDetail] = None
    summary: FCSummary = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False

        for claim in self.claim_detail:
            if not claim.attribute_check():
                print(f"Field {field.name} is None")
                return False

        self.summary.attribute_check()

        return True
