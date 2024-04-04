from __future__ import annotations

import asyncio
from openai import OpenAI
from anthropic import Anthropic
from collections import deque
import time
from factcheck.config.secret_dict import openai_dict, anthropic_dict
from functools import partial


class APIClient:
    def __init__(self, model: str) -> None:
        self.model = model
        if self.model.startswith("gpt"):
            self.client = OpenAI(api_key=openai_dict["key"])
        elif self.model.startswith("claude"):
            self.client = Anthropic(api_key=anthropic_dict["key"])
        else:
            raise ValueError("Model not supported")

    def complete(self, messages: str, seed: int):
        response = ""
        if self.model.startswith("gpt"):
            response = self._oai_call(messages, seed)
        elif self.model.startswith("claude"):
            response = self._anthropic_call(messages, seed)
        return response

    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ):
        if self.model.startswith("gpt"):
            return self._oai_construct_message_list(prompt_list, system_role)
        elif self.model.startswith("claude"):
            return self._anthropic_construct_message_list(prompt_list, system_role)

    def _oai_call(self, messages: str, seed: int):
        response = ""
        try:
            response = self.client.chat.completions.create(
                response_format={"type": "json_object"},
                seed=seed,
                model=self.model,
                messages=messages,
            )
        except Exception as e:
            print(f"Error ChatGPTClient: {e}")
            pass
        return response

    def _oai_construct_message_list(
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

    def _anthropic_call(self, messages: str, seed: int):
        response = ""
        try:
            response = self.client.messages.create(
                messages=messages,
                model=self.model,
                max_tokens=2048,
            )
        except Exception as e:
            print(f"Error ChatGPTClient: {e}")
            pass
        return response

    def _anthropic_construct_message_list(
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


class GPTClient:
    def __init__(
        self,
        model: str = None,
        max_traffic_bytes=1000000,
        max_requests_per_minute=200,
        request_window=60,
    ):
        self.max_traffic_bytes = max_traffic_bytes
        self.max_requests_per_minute = max_requests_per_minute
        self.request_window = request_window
        self.traffic_queue = deque()
        self.total_traffic = 0
        self.model = model
        self.client = APIClient(model=self.model)

    def set_model(self, model: str):
        self.model = model

    def _call(self, messages: str, seed: int):
        return self.client.complete(messages, seed)

    def multi_call(self, messages: str, num_retries=3, waiting_time=1, seed=42):
        r = ""
        for _ in range(num_retries):
            response = self._call(messages[0], seed=seed)
            try:
                r = response.choices[0].message.content
                break
            except Exception as e:
                print(f"{e}. Retrying...")
                time.sleep(waiting_time)
        return r

    def get_request_length(self, messages):
        # TODO: check if we should return the len(menages) instead
        return 1

    async def call_chatgpt_async(self, messages: list, key: str = None, seed=42):
        """Calls ChatGPT asynchronously, tracks traffic, and enforces rate limits."""
        while len(self.traffic_queue) >= self.max_requests_per_minute:
            await asyncio.sleep(1)
            self.expire_old_traffic()

        loop = asyncio.get_running_loop()
        # TODO: support seed
        response = await loop.run_in_executor(None, partial(self._call, messages, seed=seed))

        self.total_traffic += self.get_request_length(messages)
        self.traffic_queue.append((time.time(), self.get_request_length(messages)))

        result = response.choices[0].message.content
        if key:
            return key, result
        else:
            return result

    def call_chatgpt_multiple_async(self, messages_list, seed=42):
        """Calls ChatGPT asynchronously for multiple prompts and returns a list of responses."""
        tasks = [self.call_chatgpt_async(messages=messages, seed=seed) for messages in messages_list]
        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(asyncio.gather(*tasks))
        return responses

    def call_chatgpt_multiple_async_with_key(self, messages_dict):
        """Calls ChatGPT asynchronously for multiple prompts and returns a list of responses."""
        tasks = [self.call_chatgpt_async(messages=messages, key=key) for key, messages in messages_dict.items()]
        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(asyncio.gather(*tasks))
        return responses

    def expire_old_traffic(self):
        """Expires traffic older than the request window."""
        current_time = time.time()
        while self.traffic_queue and self.traffic_queue[0][0] + self.request_window < current_time:
            self.total_traffic -= self.traffic_queue.popleft()[1]

    def construct_message_dict(
        self,
        prompt_list: list[str],
        match_key_list: list[str],
        system_role: str = "You are a helpful factcheck assistant designed to output JSON.",
    ):
        assert len(prompt_list) == len(match_key_list), "match_key_list length has to be equal to prompt_list length"
        messages_dict = dict()
        for key, prompt in zip(match_key_list, prompt_list):
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt},
            ]
            messages_dict[key] = messages
        return messages_dict

    def construct_message_list(
        self,
        prompt_list: list[str],
        system_role: str = "You are a helpful assistant designed to output JSON.",
    ):
        return self.client.construct_message_list(prompt_list, system_role)


def main():
    """Example usage."""
    client = GPTClient()
    prompts = ["ping", "pong", "ping"]
    messages_list = client.construct_message_list(prompts)
    responses = client.call_chatgpt_multiple_async(messages_list)
    print(responses)

    match_key_list = ["1", "2", "3"]
    messages_dict = client.construct_message_dict(prompts, match_key_list)
    responses = client.call_chatgpt_multiple_async_with_key(messages_dict=messages_dict)
    for key, result in responses:
        print(key, ": ", result)


if __name__ == "__main__":
    main()
