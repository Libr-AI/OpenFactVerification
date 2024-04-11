from factcheck.utils.prompt import SENTENCES_TO_CLAIMS_PROMPT
from factcheck.config.CustomLogger import CustomLogger
import nltk

logger = CustomLogger(__name__).getlog()


class Decompose:
    def __init__(self, llm_client):
        """Initialize the Decompose class

        Args:
            model (str, optional): The version of the GPT model used for claim decomposition. Defaults to "gpt-3.5-turbo".
        """
        self.llm_client = llm_client
        self.doc2sent = self._nltk_doc2sent

    def _nltk_doc2sent(self, text: str):
        """Split the document into sentences using nltk

        Args:
            text (str): the document to be split into sentences

        Returns:
            list: a list of sentences
        """

        sentences = nltk.sent_tokenize(text)
        sentence_list = [s.strip() for s in sentences if len(s.strip()) >= 3]
        return sentence_list

    def getclaims(self, doc: str, num_retries: int = 3):
        """Use GPT to decompose a document into claims

        Args:
            doc (str): the document to be decomposed into claims
            num_retries (int, optional): maximum attempts for GPT to decompose the document into claims. Defaults to 3.

        Returns:
            list: a list of claims
        """
        prompt_text = SENTENCES_TO_CLAIMS_PROMPT
        user_input = prompt_text.format(doc=doc).strip()

        messages = self.llm_client.construct_message_list([user_input])
        for i in range(num_retries):
            response = self.llm_client.call(
                messages=messages,
                num_retries=1,
                seed=42 + i,
            )
            try:
                claims = eval(response)["claims"]
                if isinstance(claims, list) and len(claims) > 0:
                    return claims
            except Exception as e:
                logger.error(f"Parse chatgpt result error {e}, response is: {response}")
                logger.error(f"Parse chatgpt result error, prompt is: {messages}")

        logger.info("It does not output a list of sentences correctly, return self.doc2sent_tool split results.")
        claims = self.doc2sent(doc)
        return claims
