import os

serper_dict = {"default_key": "2608ec01b06e07513e83b4b0a0e758dfb100d635"}
openai_dict = {"default_key": "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"}
anthropic_dict = {"default_key": None}

serper_dict["key"] = os.environ.get("SERPER_API_KEY", serper_dict["default_key"])
openai_dict["key"] = os.environ.get("OPENAI_API_KEY", openai_dict["default_key"])
anthropic_dict["key"] = os.environ.get(
    "ANTHROPIC_API_KEY", anthropic_dict["default_key"]
)
