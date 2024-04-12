import time
import asyncio
from abc import abstractmethod
from collections import deque
from factcheck.config.secret_dict import openai_dict, anthropic_dict
from functools import partial


class BaseClient:
    def __init__(self, model: str) -> None:
        self.model = model

    @abstractmethod
    def _call(self, messages: str):
        """Internal function to call the API."""
        pass

    @abstractmethod
    def call(self, messages: str, num_retries) -> str:
        """API call with retries."""
        raise NotImplementedError

    @abstractmethod
    def _async_call(self, messages: list) -> str:
        """Internal function to call the API asynchronously."""
        pass

    @abstractmethod
    def multi_call(self, messages_list: list[str]) -> list[str]:
        """Multiple API calls simultaneously. It's better to support async."""
        raise NotImplementedError

    @abstractmethod
    def construct_message_list(self, prompt_list: list[str]) -> list[str]:
        """Construct a list of messages for the function self.multi_call."""
        raise NotImplementedError


class ClaudeClient(BaseClient):
    def __init__(self, model: str) -> None:
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


class ChatGPTClient(BaseClient):
    def __init__(
        self,
        model: str = None,
        max_traffic_bytes=1000000,
        max_requests_per_minute=200,
        request_window=60,
    ):
        super().__init__(model)
        from openai import OpenAI

        self.max_traffic_bytes = max_traffic_bytes
        self.max_requests_per_minute = max_requests_per_minute
        self.request_window = request_window
        self.traffic_queue = deque()
        self.total_traffic = 0
        self.client = OpenAI(api_key=openai_dict["key"])

    def set_model(self, model: str):
        self.model = model

    def _call(self, messages: str, seed: int):
        response = ""
        try:
            response = self.client.chat.completions.create(
                response_format={"type": "json_object"},
                seed=seed,
                model=self.model,
                messages=messages,
            )
        except Exception as e:
            print(f"Error ChatGPT call: {e}")
            pass
        return response

    def call(self, messages: str, num_retries=3, waiting_time=1, seed=42):
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

    async def _async_call(self, messages: list, seed=42):
        """Calls ChatGPT asynchronously, tracks traffic, and enforces rate limits."""
        while len(self.traffic_queue) >= self.max_requests_per_minute:
            await asyncio.sleep(1)
            self.expire_old_traffic()

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, partial(self._call, messages, seed=seed))

        self.total_traffic += self.get_request_length(messages)
        self.traffic_queue.append((time.time(), self.get_request_length(messages)))

        result = response.choices[0].message.content
        return result

    def multi_call(self, messages_list, seed=42):
        tasks = [self._async_call(messages=messages, seed=seed) for messages in messages_list]
        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(asyncio.gather(*tasks))
        return responses

    def expire_old_traffic(self):
        """Expires traffic older than the request window."""
        current_time = time.time()
        while self.traffic_queue and self.traffic_queue[0][0] + self.request_window < current_time:
            self.total_traffic -= self.traffic_queue.popleft()[1]

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


def main():
    """Example usage."""
    client = ChatGPTClient()
    prompts = ["ping", "pong", "ping"]
    messages_list = client.construct_message_list(prompts)
    responses = client.multi_call(messages_list)
    print(responses)


if __name__ == "__main__":
    main()
