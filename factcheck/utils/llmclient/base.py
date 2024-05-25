import time
import asyncio
from abc import abstractmethod
from functools import partial
from collections import deque

from ..data_class import TokenUsage


class BaseClient:
    def __init__(
        self,
        model: str,
        api_config: dict,
        max_requests_per_minute: int,
        request_window: int,
    ) -> None:
        self.model = model
        self.api_config = api_config
        self.max_requests_per_minute = max_requests_per_minute
        self.request_window = request_window
        self.traffic_queue = deque()
        self.total_traffic = 0
        self.usage = TokenUsage(model=model)

    @abstractmethod
    def _call(self, messages: str):
        """Internal function to call the API."""
        pass

    @abstractmethod
    def _log_usage(self):
        """Log the usage of tokens, should be used in each client's _call method."""
        pass

    def get_usage(self):
        return self.usage

    def reset_usage(self):
        self.usage.prompt_tokens = 0
        self.usage.completion_tokens = 0

    @abstractmethod
    def construct_message_list(self, prompt_list: list[str]) -> list[str]:
        """Construct a list of messages for the function self.multi_call."""
        raise NotImplementedError

    @abstractmethod
    def get_request_length(self, messages):
        """Get the length of the request. Used for tracking traffic."""
        raise NotImplementedError

    def call(self, messages: list[str], num_retries=3, waiting_time=1, **kwargs):
        seed = kwargs.get("seed", 42)
        assert type(seed) is int, "Seed must be an integer."
        assert len(messages) == 1, "Only one message is allowed for this function."

        r = ""
        for _ in range(num_retries):
            try:
                r = self._call(messages[0], seed=seed)
                break
            except Exception as e:
                print(f"Error LLM Client call: {e} Retrying...")
                time.sleep(waiting_time)

        if r == "":
            raise ValueError("Failed to get response from LLM Client.")
        return r

    def set_model(self, model: str):
        self.model = model

    async def _async_call(self, messages: list, **kwargs):
        """Calls ChatGPT asynchronously, tracks traffic, and enforces rate limits."""
        while len(self.traffic_queue) >= self.max_requests_per_minute:
            await asyncio.sleep(1)
            self._expire_old_traffic()

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, partial(self._call, messages, **kwargs))

        self.total_traffic += self.get_request_length(messages)
        self.traffic_queue.append((time.time(), self.get_request_length(messages)))

        return response

    def multi_call(self, messages_list, **kwargs):
        tasks = [self._async_call(messages=messages, **kwargs) for messages in messages_list]
        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(asyncio.gather(*tasks))
        return responses

    def _expire_old_traffic(self):
        """Expires traffic older than the request window."""
        current_time = time.time()
        while self.traffic_queue and self.traffic_queue[0][0] + self.request_window < current_time:
            self.total_traffic -= self.traffic_queue.popleft()[1]
