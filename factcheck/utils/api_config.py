import os

# Define all keys for the API configuration
keys = [
    "SERPER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "LOCAL_API_KEY",
    "LOCAL_API_URL",
]


def load_api_config(api_config: dict = None):
    """Load API keys from environment variables or config file, config file take precedence

    Args:
        api_config (dict, optional): _description_. Defaults to None.
    """
    if api_config is None:
        api_config = dict()
    assert type(api_config) is dict, "api_config must be a dictionary."

    merged_config = {}

    for key in keys:
        merged_config[key] = api_config.get(key, None)
        if merged_config[key] is None:
            merged_config[key] = os.environ.get(key, None)

    for key in api_config.keys():
        if key not in keys:
            merged_config[key] = api_config[key]
    return merged_config
