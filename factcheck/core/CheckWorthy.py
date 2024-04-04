from typing import List
from factcheck.utils.prompt import CHECKWORTHY_PROMPT
from factcheck.utils.GPTClient import GPTClient
from factcheck.config.CustomLogger import CustomLogger

logger = CustomLogger(__name__).getlog()


class Checkworthy:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """Initialize the Checkworthy class

        Args:
            model (str, optional): The version of the GPT model used for checkworthy classification. Defaults to "gpt-3.5-turbo".
        """
        self.chatgpt_client = GPTClient(model=model)

    def identify_checkworthiness(self, texts: List[str], num_retries: int = 3) -> List[str]:
        """Use GPT to identify whether candidate claims are worth fact checking. if gpt is unable to return correct checkworthy_claims, we assume all texts are checkworthy.

        Args:
            texts (List[str]): a list of texts to identify whether they are worth fact checking
            num_retries (int, optional): maximum attempts for GPT to identify checkworthy claims. Defaults to 3.

        Returns:
            List[str]: a list of checkworthy claims, pairwise outputs
        """
        checkworthy_claims = texts
        # TODO: better handle checkworthiness
        joint_texts = "\n".join([str(i + 1) + ". " + j for i, j in enumerate(texts)])
        user_input = CHECKWORTHY_PROMPT.format(texts=joint_texts)
        messages = self.chatgpt_client.construct_message_list([user_input])
        for i in range(num_retries):
            response = self.chatgpt_client.multi_call(messages, num_retries=1, seed=42 + i)
            try:
                results = eval(response)
                valid_answer = list(
                    filter(
                        lambda x: x[1].startswith("Yes") or x[1].startswith("No"),
                        results.items(),
                    )
                )
                checkworthy_claims = list(filter(lambda x: x[1].startswith("Yes"), results.items()))
                checkworthy_claims = list(map(lambda x: x[0], checkworthy_claims))
                assert len(valid_answer) == len(results)
                break
            except Exception as e:
                logger.error(f"====== Error: {e}, the response is: {response}")
                logger.error(f"====== Our input is: {messages}")
        return checkworthy_claims, results
