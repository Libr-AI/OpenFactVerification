import yaml
from factcheck.utils.prompt.base import BasePrompt


class CustomizedPrompt(BasePrompt):
    def __init__(self, CustomizedPrompt):
        self.prompts = self.load_prompt_yaml(CustomizedPrompt)
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
