from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class QueryGenerator:
    def __init__(self, llm_client, prompt, max_query_per_claim: int = 5):
        """Initialize the QueryGenerator class

        Args:
            llm_client (BaseClient): The LLM client used for generating questions.
            prompt (BasePrompt): The prompt used for generating questions.
        """
        self.llm_client = llm_client
        self.prompt = prompt
        self.max_query_per_claim = max_query_per_claim

    def generate_query(self, claims: list[str], generating_time: int = 3, prompt: str = None) -> dict[str, list[str]]:
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
            if prompt is None:
                user_input = self.prompt.qgen_prompt.format(claim=claim)
            else:
                user_input = prompt.format(claim=claim)
            messages_list.append(user_input)

        while (attempts < generating_time) and ([] in generated_questions):
            _messages = [_message for _i, _message in enumerate(messages_list) if generated_questions[_i] == []]
            _indices = [_i for _i, _message in enumerate(messages_list) if generated_questions[_i] == []]

            _message_list = self.llm_client.construct_message_list(_messages)
            _response_list = self.llm_client.multi_call(_message_list)

            for _response, _index in zip(_response_list, _indices):
                try:
                    _questions = eval(_response)["Questions"]
                    generated_questions[_index] = _questions
                except:  # noqa: E722
                    logger.info(f"Warning: LLM response parse fail, retry {attempts}.")
            attempts += 1

        # ensure that each claim has at least one question which is the claim itself
        claim_query_dict = {
            _claim: [_claim] + _generated_questions[: (self.max_query_per_claim - 1)]
            for _claim, _generated_questions in zip(claims, generated_questions)
        }
        return claim_query_dict
