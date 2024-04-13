import time
import asyncio
from abc import abstractmethod
from functools import partial
from collections import deque


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

    @abstractmethod
    def _call(self, messages: str):
        """Internal function to call the API."""
        pass

    @abstractmethod
    def call(self, messages: str, num_retries) -> str:
        """API call with retries."""
        raise NotImplementedError

    @abstractmethod
    def construct_message_list(self, prompt_list: list[str]) -> list[str]:
        """Construct a list of messages for the function self.multi_call."""
        raise NotImplementedError

    @abstractmethod
    def get_request_length(self, messages):
        """Get the length of the request. Used for tracking traffic."""
        raise NotImplementedError

    def set_model(self, model: str):
        self.model = model

    async def _async_call(self, messages: list, **kwargs):
        """Calls ChatGPT asynchronously, tracks traffic, and enforces rate limits."""
        while len(self.traffic_queue) >= self.max_requests_per_minute:
            await asyncio.sleep(1)
            self.expire_old_traffic()

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, partial(self._call, messages, **kwargs)
        )

        self.total_traffic += self.get_request_length(messages)
        self.traffic_queue.append((time.time(), self.get_request_length(messages)))

        return response

    def multi_call(self, messages_list, **kwargs):
        tasks = [
            self._async_call(messages=messages, **kwargs) for messages in messages_list
        ]
        asyncio.set_event_loop(asyncio.SelectorEventLoop())
        loop = asyncio.get_event_loop()
        responses = loop.run_until_complete(asyncio.gather(*tasks))
        return responses

    def expire_old_traffic(self):
        """Expires traffic older than the request window."""
        current_time = time.time()
        while (
            self.traffic_queue
            and self.traffic_queue[0][0] + self.request_window < current_time
        ):
            self.total_traffic -= self.traffic_queue.popleft()[1]
