from dataclasses import dataclass


@dataclass
class BasePrompt:
    decompose_prompt: str = None
    checkworthy_prompt: str = None
    qgen_prompt: str = None
    verify_prompt: str = None
