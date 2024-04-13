import os
import time
import asyncio
from abc import abstractmethod
from collections import deque
from functools import partial

from openai import OpenAI

from factcheck.config.secret_dict import openai_dict, anthropic_dict
from factcheck.utils.llmclient.base import BaseClient


class ClaudeClient(BaseClient):
    def __init__(self, model: str, api_config: dict) -> None:
        super().__init__(model)
        from anthropic import Anthropic

        self.client = Anthropic(api_key=anthropic_dict["key"])

    def _call(self, messages: str, seed: int):
        response = ""
        try:
            response = self.client.messages.create(
                messages=messages,
                model=self.model,
                max_tokens=2048,
            )
        except Exception as e:
            print(f"Error Claude call: {e}")
            pass
        return response

    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ):
        # system role is not used in this case
        messages_list = list()
        for prompt in prompt_list:
            messages = [
                {"role": "user", "content": prompt},
            ]
            messages_list.append(messages)
        return messages_list
