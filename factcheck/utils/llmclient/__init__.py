from .gpt_client import GPTClient
from .claude_client import ClaudeClient
from .local_openai_client import LocalOpenAIClient

# fmt: off
CLIENTS = {
    "gpt": GPTClient,
    "claude": ClaudeClient,
    "local_openai": LocalOpenAIClient
}
# fmt: on


def model2client(model_name: str):
    """If the client is not specified, use this function to map the model name to the corresponding client."""
    if model_name.startswith("gpt"):
        return GPTClient
    elif model_name.startswith("claude"):
        return ClaudeClient
    elif model_name.startswith("vicuna"):
        return LocalOpenAIClient
    else:
        raise ValueError(f"Model {model_name} not supported.")
