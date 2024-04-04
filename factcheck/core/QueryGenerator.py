from __future__ import annotations
from factcheck.utils.prompt import QGEN_PROMPT
from factcheck.utils.GPTClient import GPTClient
from factcheck.config.CustomLogger import CustomLogger

logger = CustomLogger(__name__).getlog()


class QueryGenerator:
    def __init__(self, model: str = "gpt-3.5-turbo") -> None:
        """Initialize the QueryGenerator class

        Args:
            model (str, optional): The version of the GPT model used for query generation. Defaults to "gpt-3.5-turbo".
        """
        self.chatgpt_client = GPTClient(model=model)
        self.max_query_per_claim = 5

    def generate_query(self, claims: list[str], generating_time: int = 3):
        """Generate questions for the given claims

        Args:
            claims ([str]): a list of claims to generate questions for.
            generating_time (int, optional): maximum attempts for GPT to generate questions. Defaults to 3.

        Returns:
            dict: a dictionary of claims and their corresponding generated questions.
        """
        generated_questions = [[]] * len(claims)
        attempts = 0

        # construct messages
        messages_list = []
        for claim in claims:
            user_input = QGEN_PROMPT.format(claim=claim)
            messages_list.append(user_input)

        while (attempts < generating_time) and ([] in generated_questions):
            _messages = [_message for _i, _message in enumerate(messages_list) if generated_questions[_i] == []]
            _indices = [_i for _i, _message in enumerate(messages_list) if generated_questions[_i] == []]

            _message_list = self.chatgpt_client.construct_message_list(_messages)
            _response_list = self.chatgpt_client.call_chatgpt_multiple_async(_message_list)

            for _response, _index in zip(_response_list, _indices):
                try:
                    _questions = eval(_response)["Questions"]
                    generated_questions[_index] = _questions
                except:  # noqa: E722
                    logger.info(f"Warning: ChatGPT response parse fail, retry {attempts}.")
            attempts += 1

        # ensure that each claim has at least one question which is the claim itself
        claim_query_dict = {
            _claim: [_claim] + _generated_questions[: (self.max_query_per_claim - 1)]
            for _claim, _generated_questions in zip(claims, generated_questions)
        }
        return claim_query_dict
