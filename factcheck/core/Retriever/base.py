from concurrent.futures import ProcessPoolExecutor
import os
from copy import deepcopy
from factcheck.utils.web_util import parse_response, crawl_web
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class BaseRetriever:
    def __init__(self, llm_client, api_config: dict = None):
        """Initialize the EvidenceRetrieve class."""
        import spacy

        self.tokenizer = spacy.load("en_core_web_sm", disable=["ner", "tagger", "lemmatizer"])
        from sentence_transformers import CrossEncoder
        import torch

        self.passage_ranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=512,
            device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        )
        self.lang = "en"
        self.max_search_result_per_query = 3
        self.sentences_per_passage = 10
        self.sliding_distance = 8
        self.max_passages_per_search_result_to_return = 5
        assert self.sentences_per_passage > self.sliding_distance
        self.llm_client = llm_client

    def set_lang(self, lang: str):
        """Set the language for evidence retrieval.

        Args:
            lang (str): The language for evidence retrieval.
        """
        self.lang = lang

    def set_max_search_result_per_query(self, m: int):
        """Set the maximum number of search results per query.

        Args:
            m (int): The maximum number of search results per query.
        """
        self.max_search_result_per_query = m

    def retrieve_evidence(self, claim_query_dict):
        """Retrieve evidence for a list of claims.
        1. get google search page result by generated questions
        2. crawl all web from urls and extract text
        3. get relevant snippets from these text
        4. Take top-5 evidences for each question
        5. return single claims evidences;

        Args:
            claim_query_dict (dict): A dictionary of claims and their corresponding queries.

        Returns:
            dict: A dictionary of claims and their corresponding evidences.
        """
        claim_evidence_dict = {}
        for claim, query_list in claim_query_dict.items():
            logger.info(f"Collecting evidences for claim : {claim}")
            evidences = self._retrieve_evidence4singleclaim(claim, query_list=query_list)
            claim_evidence_dict[claim] = evidences
        return claim_evidence_dict

    def _retrieve_evidence4singleclaim(self, claim: str, query_list: list[str]):
        """Retrieve evidence for a single claim.

        Args:
            claim (str): The claim to retrieve evidence for.
            query_list (list[str]): A list of queries for the claim.

        Returns:
            dict: A dictionary of claims and their corresponding evidences.
        """

        query_url_dict = self._get_query_urls(query_list)
        query_scraped_results_dict = self._crawl_and_parse_web(query_url_dict=query_url_dict)
        evidences = self._get_relevant_snippets(query_scraped_results_dict=query_scraped_results_dict)
        return evidences

    def _crawl_and_parse_web(self, query_url_dict: dict[str, list]):
        responses = crawl_web(query_url_dict=query_url_dict)
        query_responses_dict = dict()
        for flag, response, url, query in responses:
            if flag and ".pdf" not in str(response.url):
                response_list = query_responses_dict.get(query, [])
                response_list.append([response, url])
                query_responses_dict[query] = response_list

        query_scraped_results_dict = dict()
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            futures = list()
            for query, response_list in query_responses_dict.items():
                for response, url in response_list:
                    future = executor.submit(parse_response, response, url, query)
                    futures.append(future)
        for future in futures:
            web_text, url, query = future.result()
            scraped_results_list = query_scraped_results_dict.get(query, [])
            scraped_results_list.append([web_text, url])
            query_scraped_results_dict[query] = scraped_results_list
        # Remove URLs if we weren't able to scrape anything or if they are a PDF.
        for query in query_scraped_results_dict.keys():
            scraped_results_list = query_scraped_results_dict.get(query)
            # remove if crawled web text is null
            scraped_results = [pair for pair in scraped_results_list if pair[0]]
            # get top scraped results by self.max_search_result_per_query
            query_scraped_results_dict[query] = scraped_results[: self.max_search_result_per_query]
        # print("query_scraped_res", query_scraped_results_dict)
        return query_scraped_results_dict

    def _get_relevant_snippets(self, query_scraped_results_dict: dict[str:list]):
        """Get relevant snippets from the scraped web text.

        Args:
            query_scraped_results_dict (dict): A dictionary of queries and their corresponding scraped web text.

        Returns:
            dict: A dictionary of queries and their corresponding relevant snippets.
        """
        # 4+ 5 chunk to split web text to several passage and score and sort
        snippets_dict = {}
        for query, scraped_results in query_scraped_results_dict.items():
            snippets_dict[query] = self._sorted_passage_by_relevant_score(query, scraped_results=scraped_results)
            snippets_dict[query] = deepcopy(
                sorted(
                    snippets_dict[query],
                    key=lambda snippet: snippet["retrieval_score"],
                    reverse=True,
                )[:5]
            )

        evidences = {}
        evidences["aggregated"] = []
        evidences["question_wise"] = deepcopy(snippets_dict)
        for key in evidences["question_wise"]:
            # Take top evidences for each question
            index = int(len(evidences["aggregated"]) / len(evidences["question_wise"]))
            evidences["aggregated"].append(evidences["question_wise"][key][index])
            if len(evidences["aggregated"]) >= self.max_passages_per_search_result_to_return:
                break
        # 6
        return evidences["aggregated"]

    def _sorted_passage_by_relevant_score(self, query: str, scraped_results: list[str]):
        """Sort the passages by relevance to the query using a cross-encoder.

        Args:
            query (str): The query to sort the passages by relevance.
            scraped_results (list[str]): A list of scraped web text.

        Returns:
            list: a list of relevant snippets, where each snippet is a dictionary containing the text, url, sentences per passage, and retrieval score.
        """
        retrieved_passages = list()
        weball = ""
        for webtext, url in scraped_results:
            weball += webtext
        passages = self._chunk_text(text=weball, tokenizer=self.tokenizer)
        if not passages:
            return []
        # Score the passages by relevance to the query using a cross-encoder.
        scores = self.passage_ranker.predict([(query, p[0]) for p in passages]).tolist()
        passage_scores = list(zip(passages, scores))

        # Take the top passages_per_search passages for the current search result.
        passage_scores.sort(key=lambda x: x[1], reverse=True)

        relevant_items = list()
        for passage_item, score in passage_scores:
            overlap = False
            if len(relevant_items) > 0:
                for item in relevant_items:
                    if passage_item[1] >= item[1] and passage_item[1] <= item[2]:
                        overlap = True
                        break
                    if passage_item[2] >= item[1] and passage_item[2] <= item[2]:
                        overlap = True
                        break

            # Only consider top non-overlapping relevant passages to maximise for information
            if not overlap:
                relevant_items.append(deepcopy(passage_item))
                retrieved_passages.append(
                    {
                        "text": passage_item[0],
                        "url": url,
                        "sents_per_passage": self.sentences_per_passage,
                        "retrieval_score": score,  # Cross-encoder score as retr score
                    }
                )
            if len(relevant_items) >= self.max_passages_per_search_result_to_return:
                break
        # print("Total snippets extracted: ", len(retrieved_passages))
        return retrieved_passages

    def _chunk_text(
        self,
        text: str,
        tokenizer,
        min_sentence_len: int = 3,
        max_sentence_len: int = 250,
    ) -> list[str]:
        """Chunks text into passages using a sliding window.

        Args:
            text: Text to chunk into passages.
            max_sentence_len: Maximum number of chars of each sentence before being filtered.
        Returns:
            passages: Chunked passages from the text.
        """
        passages = []
        try:
            logger.info("========web text len: {} =======".format((len(text))))
            doc = tokenizer(text[:500000])  # Take 500k chars to not break tokenization.
            sents = [
                s.text.replace("\n", " ")
                for s in doc.sents
                if min_sentence_len <= len(s.text) <= max_sentence_len  # Long sents are usually metadata.
            ]
            for idx in range(0, len(sents), self.sliding_distance):
                passages.append(
                    (
                        " ".join(sents[idx : idx + self.sentences_per_passage]),
                        idx,
                        idx + self.sentences_per_passage - 1,
                    )
                )
        except UnicodeEncodeError as e:  # Sometimes run into Unicode error when tokenizing.
            logger.error(f"Unicode error when using Spacy. Skipping text. Error message {e}")
        return passages
