import time
from anthropic import Anthropic
from .base import BaseClient


class ClaudeClient(BaseClient):
    def __init__(
        self,
        model: str = "claude-3-opus-20240229",
        api_config: dict = None,
        max_requests_per_minute=200,
        request_window=60,
    ):
        super().__init__(model, api_config, max_requests_per_minute, request_window)
        self.client = Anthropic(api_key=self.api_config["ANTHROPIC_API_KEY"])

    def _call(self, messages: str, **kwargs):
        response = self.client.messages.create(
            messages=messages,
            model=self.model,
            max_tokens=2048,
        )
        return response.content[0].text

    def get_request_length(self, messages):
        return 1

    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = None,
    ):
        if system_role is None:
            Warning("system_role is not used in this case")
        # system role is not used in this case
        messages_list = list()
        for prompt in prompt_list:
            messages = [
                {"role": "user", "content": prompt},
            ]
            messages_list.append(messages)
        return messages_list
