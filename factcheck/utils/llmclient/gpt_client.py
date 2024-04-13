import os
import time
import asyncio
from abc import abstractmethod
from collections import deque
from functools import partial

from openai import OpenAI

from factcheck.config.secret_dict import openai_dict, anthropic_dict
from factcheck.utils.llmclient.base import BaseClient


class GPTClient(BaseClient):
    def __init__(
        self,
        model: str = "gpt-4-turbo",
        api_config: dict = None,
        max_requests_per_minute=200,
        request_window=60,
    ):
        super().__init__(model, api_config, max_requests_per_minute, request_window)
        self.client = OpenAI(api_key=self.api_config["OPENAI_API_KEY"])

    def _call(self, messages: str, **kwargs):
        seed = kwargs.get("seed", 42)  # default seed is 42
        assert type(seed) is int, "Seed must be an integer."

        response = self.client.chat.completions.create(
            response_format={"type": "json_object"},
            seed=seed,
            model=self.model,
            messages=messages,
        )
        r = response.choices[0].message.content
        return r

    def call(self, messages: str, num_retries=3, waiting_time=1, **kwargs):
        seed = kwargs.get("seed", 42)
        assert type(seed) is int, "Seed must be an integer."

        r = ""
        for _ in range(num_retries):
            try:
                r = self._call(messages[0], seed=seed)
                break
            except Exception as e:
                print(f"Error ChatGPT call: {e} Retrying...")
                time.sleep(waiting_time)

        if r == "":
            raise ValueError("Failed to get response from ChatGPT.")
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
