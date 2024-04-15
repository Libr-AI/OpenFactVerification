import yaml
import json
from .base import BasePrompt


class CustomizedPrompt(BasePrompt):
    def __init__(self, CustomizedPrompt):
        if CustomizedPrompt.endswith("yaml"):
            self.prompts = self.load_prompt_yaml(CustomizedPrompt)
        elif CustomizedPrompt.endswith("json"):
            self.prompts = self.load_prompt_json(CustomizedPrompt)
        else:
            raise NotImplementedError(f"File type of {CustomizedPrompt} not implemented.")
        keys = [
            "decompose_prompt",
            "checkworthy_prompt",
            "qgen_prompt",
            "verify_prompt",
        ]

        for key in keys:
            assert key in self.prompts, f"Key {key} not found in the prompt yaml file."
            setattr(self, key, self.prompts[key])

    def load_prompt_yaml(self, prompt_name):
        # Load the prompt from a yaml file
        with open(prompt_name, "r") as file:
            return yaml.safe_load(file)

    def load_prompt_json(self, prompt_name):
        # Load the prompt from a json file
        with open(prompt_name, "r") as file:
            return json.load(file)
