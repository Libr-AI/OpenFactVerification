from factcheck.utils.llmclient.gpt_client import GPTClient
from factcheck.utils.llmclient.claude_client import ClaudeClient


def model2client(model_name: str):
    # router for model to client
    if model_name.startswith("gpt"):
        return GPTClient
    elif model_name.startswith("claude"):
        return ClaudeClient
    else:
        raise ValueError(f"Model {model_name} not supported.")
