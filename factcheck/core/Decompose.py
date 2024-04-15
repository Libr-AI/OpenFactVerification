from factcheck.utils.logger import CustomLogger
import nltk

logger = CustomLogger(__name__).getlog()


class Decompose:
    def __init__(self, llm_client, prompt):
        """Initialize the Decompose class

        Args:
            llm_client (BaseClient): The LLM client used for decomposing documents into claims.
            prompt (BasePrompt): The prompt used for fact checking.
        """
        self.llm_client = llm_client
        self.prompt = prompt
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

    def getclaims(self, doc: str, num_retries: int = 3, prompt: str = None):
        """Use GPT to decompose a document into claims

        Args:
            doc (str): the document to be decomposed into claims
            num_retries (int, optional): maximum attempts for GPT to decompose the document into claims. Defaults to 3.

        Returns:
            list: a list of claims
        """
        if prompt is None:
            user_input = self.prompt.decompose_prompt.format(doc=doc).strip()
        else:
            user_input = prompt.format(doc=doc).strip()

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
                logger.error(f"Parse LLM response error {e}, response is: {response}")
                logger.error(f"Parse LLM response error, prompt is: {messages}")

        logger.info("It does not output a list of sentences correctly, return self.doc2sent_tool split results.")
        claims = self.doc2sent(doc)
        return claims
