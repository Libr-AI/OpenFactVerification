import time

import openai
from openai import OpenAI
from factcheck.utils.llmclient.base import BaseClient


class LocalClient(BaseClient):
    def __init__(
        self,
        model: str = "gpt-4-turbo",
        api_config: dict = None,
        max_requests_per_minute=200,
        request_window=60,
    ):
        super().__init__(model, api_config, max_requests_per_minute, request_window)

        openai.api_key = "EMPTY"
        openai.base_url = "http://localhost:8000/v1/"

    def _call(self, messages: str, **kwargs):
        seed = kwargs.get("seed", 42)  # default seed is 42
        assert type(seed) is int, "Seed must be an integer."

        response = openai.chat.completions.create(
            response_format={"type": "json_object"},
            seed=seed,
            model=self.model,
            messages=messages,
        )
        r = response.choices[0].message.content
        return r

    def get_request_length(self, messages):
        # TODO: check if we should return the len(menages) instead
        return 1

    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ):
        messages_list = list()
        for prompt in prompt_list:
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt},
            ]
            messages_list.append(messages)
        return messages_list
