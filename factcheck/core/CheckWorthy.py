from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class Checkworthy:
    def __init__(self, llm_client, prompt):
        """Initialize the Checkworthy class

        Args:
            llm_client (BaseClient): The LLM client used for identifying checkworthiness of claims.
            prompt (BasePrompt): The prompt used for identifying checkworthiness of claims.
        """
        self.llm_client = llm_client
        self.prompt = prompt

    def identify_checkworthiness(self, texts: list[str], num_retries: int = 3, prompt: str = None) -> list[str]:
        """Use GPT to identify whether candidate claims are worth fact checking. if gpt is unable to return correct checkworthy_claims, we assume all texts are checkworthy.

        Args:
            texts (list[str]): a list of texts to identify whether they are worth fact checking
            num_retries (int, optional): maximum attempts for GPT to identify checkworthy claims. Defaults to 3.

        Returns:
            list[str]: a list of checkworthy claims, pairwise outputs
        """
        checkworthy_claims = texts
        joint_texts = "\n".join([str(i + 1) + ". " + j for i, j in enumerate(texts)])

        if prompt is None:
            user_input = self.prompt.checkworthy_prompt.format(texts=joint_texts)
        else:
            user_input = prompt.format(texts=joint_texts)

        messages = self.llm_client.construct_message_list([user_input])
        for i in range(num_retries):
            response = self.llm_client.call(messages, num_retries=1, seed=42 + i)
            try:
                claim2checkworthy = eval(response)
                valid_answer = list(
                    filter(
                        lambda x: x[1].startswith("Yes") or x[1].startswith("No"),
                        claim2checkworthy.items(),
                    )
                )
                checkworthy_claims = list(filter(lambda x: x[1].startswith("Yes"), claim2checkworthy.items()))
                checkworthy_claims = list(map(lambda x: x[0], checkworthy_claims))
                assert len(valid_answer) == len(claim2checkworthy)
                break
            except Exception as e:
                logger.error(f"====== Error: {e}, the LLM response is: {response}")
                logger.error(f"====== Our input is: {messages}")
        return checkworthy_claims, claim2checkworthy
