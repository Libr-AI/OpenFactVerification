from .chatgpt_prompt import ChatGPTPrompt
from .claude_prompt import ClaudePrompt
from .customized_prompt import CustomizedPrompt

prompt_map = {
    "chatgpt_prompt": ChatGPTPrompt,
    "claude_prompt": ClaudePrompt,
}


def prompt_mapper(prompt_name: str):
    if prompt_name in prompt_map:
        return prompt_map[prompt_name]()
    elif prompt_name.endswith("yaml") or prompt_name.endswith("json"):
        return CustomizedPrompt(prompt_name)
    else:
        raise NotImplementedError(f"Prompt {prompt_name} not implemented.")
