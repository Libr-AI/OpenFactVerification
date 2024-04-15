from .gpt_client import GPTClient
from .claude_client import ClaudeClient
from .local_client import LocalClient


def client_mapper(model_name: str):
    # router for model to client
    if model_name.startswith("gpt"):
        return GPTClient
    elif model_name.startswith("claude"):
        return ClaudeClient
    elif model_name.startswith("vicuna"):
        return LocalClient
    else:
        raise ValueError(f"Model {model_name} not supported.")
