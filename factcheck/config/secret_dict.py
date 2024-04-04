import os

serper_dict = {"default_key": None}
openai_dict = {"default_key": None}
anthropic_dict = {"default_key": None}

serper_dict["key"] = os.environ.get("SERPER_API_KEY", serper_dict["default_key"])
openai_dict["key"] = os.environ.get("OPENAI_API_KEY", openai_dict["default_key"])
anthropic_dict["key"] = os.environ.get(
    "ANTHROPIC_API_KEY", anthropic_dict["default_key"]
)
