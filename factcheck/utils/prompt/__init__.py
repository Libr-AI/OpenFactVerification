from factcheck.utils.prompt.chatgpt_prompt import ChatGPTPrompt
from factcheck.utils.prompt.claude_prompt import ClaudePrompt

prompt_map = {
    "chatgpt_prompt": ChatGPTPrompt,
    "claude_prompt": ClaudePrompt,
}


def prompt_mapper(prompt_name: str):
    if prompt_name in prompt_map:
        return prompt_map[prompt_name]
    else:
        raise NotImplementedError(f"Prompt {prompt_name} not implemented.")
