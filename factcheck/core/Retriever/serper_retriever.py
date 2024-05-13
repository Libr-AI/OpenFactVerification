from concurrent.futures import ThreadPoolExecutor
import json
import requests
import os
import re
import bs4
from factcheck.utils.logger import CustomLogger
from factcheck.utils.web_util import crawl_web

logger = CustomLogger(__name__).getlog()


class SerperEvidenceRetriever:
    def __init__(self, api_config: dict = None):
        """Initialize the SerperEvidenceRetrieve class"""
        self.lang = "en"
        self.serper_key = api_config["SERPER_API_KEY"]

    def retrieve_evidence(self, claim_query_dict, top_k: int = 5, snippet_extend_flag: bool = True):
        """Retrieve evidences for the given claims

        Args:
            claim_query_dict (dict): a dictionary of claims and their corresponding queries.
            top_k (int, optional): the number of top relevant results to retrieve. Defaults to 5.
            snippet_extend_flag (bool, optional): whether to extend the snippet. Defaults to True.

        Returns:
            dict: a dictionary of claims and their corresponding evidences.
        """
        logger.info("Collecting evidences ...")
        claim_query_dict_L = list(claim_query_dict.items())
        query_list = [y for x in claim_query_dict_L for y in x[1]]
        evidence_list = self._retrieve_evidence_4_all_claim(
            query_list=query_list, top_k=top_k, snippet_extend_flag=snippet_extend_flag
        )

        i = 0
        claim_evidence_dict = {}
        for claim, queries in claim_query_dict_L:
            claim_evidence_dict[claim] = evidence_list[i : i + len(queries)]
            i += len(queries)
        assert i == len(evidence_list)
        logger.info("Collect evidences done!")
        return claim_evidence_dict

    def _retrieve_evidence_4_all_claim(self, query_list: list[str], top_k: int = 5, snippet_extend_flag: bool = True):
        """Retrieve evidences for the given queries

        Args:
            query_list (list[str]): a list of queries to retrieve evidences for.
            top_k (int, optional): the number of top relevant results to retrieve. Defaults to 5.
            snippet_extend_flag (bool, optional): whether to extend the snippet. Defaults to True.

        Returns:
            _type_: _description_
        """

        # init the evidence list with None
        evidences = [None] * len(query_list)

        # get the response from serper
        serper_response = self._request_serper_api(query_list)

        if serper_response is None:
            logger.error("Serper API request error!")
            return evidences

        # get the results for queries with an answer box
        query_url_dict = {}
        url_to_date = {}  # TODO: decide whether to use date
        _snippet_to_check = []
        for i, (query, result) in enumerate(zip(query_list, serper_response.json())):
            if query != result.get("searchParameters").get("q"):
                logger.error("Serper change query from {} TO {}".format(query, result.get("searchParameters").get("q")))

            if "answerBox" in result:
                if "answer" in result["answerBox"]:
                    evidences[i] = {
                        "text": f"{query}\nAnswer: {result['answerBox']['answer']}",
                        "url": "Google Answer Box",
                    }
                else:
                    evidences[i] = {
                        "text": f"{query}\nAnswer: {result['answerBox']['snippet']}",
                        "url": "Google Answer Box",
                    }
            else:
                results = result.get("organic", [])[:top_k]  # Choose top 5 result
                merge_evidence_text = [f"Text: {_result['snippet']} \n Source: {_result['link']}" for _result in results]
                merge_evidence_text = [re.sub(r"\n+", "\n", evidence) for evidence in merge_evidence_text]
                evidences[i] = {
                    "text": "\n\n".join(merge_evidence_text),
                    "url": "Multiple",
                }

                # Save date for each url
                url_to_date.update({result.get("link"): result.get("date") for result in results})
                # Save query-url pair, 1 query may have multiple urls
                query_url_dict.update({query: [result.get("link") for result in results]})
                _snippet_to_check += [result["snippet"] for result in results]

        # return if there is no snippet to check or snippet_extend_flag is False
        if (len(_snippet_to_check) == 0) or (not snippet_extend_flag):
            return evidences

        # crawl web for queries without answer box
        responses = crawl_web(query_url_dict)
        # Get extended snippets based on the snippet from serper
        flag_to_check = [_item[0] for _item in responses]
        response_to_check = [_item[1] for _item in responses]
        url_to_check = [_item[2] for _item in responses]
        query_to_check = [_item[3] for _item in responses]

        def bs4_parse_text(response, snippet, flag):
            """Parse the text from the response and extend the snippet

            Args:
                response (web response): the response from the web
                snippet (str): the snippet to extend from the search result
                flag (bool): flag to extend the snippet

            Returns:
                _type_: _description_
            """
            if flag and ".pdf" not in str(response.url):
                soup = bs4.BeautifulSoup(response.text, "html.parser")
                text = soup.get_text()
                # Search for the snippet in text
                snippet_start = text.find(snippet[:-10])
                if snippet_start == -1:
                    return snippet
                else:
                    pre_context_range = 0  # Number of characters around the snippet to display
                    post_context_range = 500  # Number of characters around the snippet to display
                    start = max(0, snippet_start - pre_context_range)
                    end = snippet_start + len(snippet) + post_context_range
                    return text[start:end] + " ..."
            else:
                return snippet

        # Question: if os.cpu_count() cause problems when running in parallel?
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            _extended_snippet = list(
                executor.map(
                    lambda _r, _s, _f: bs4_parse_text(_r, _s, _f),
                    response_to_check,
                    _snippet_to_check,
                    flag_to_check,
                )
            )

        # merge the snippets by query
        query_snippet_dict = {}
        for _query, _snippet in zip(query_to_check, _extended_snippet):
            _snippet_list = query_snippet_dict.get(_query, [])
            _snippet_list.append(_snippet)
            query_snippet_dict[_query] = _snippet_list

        # extend the evidence list for each query
        for _query in query_snippet_dict.keys():
            _query_index = query_list.index(_query)
            _snippet_list = query_snippet_dict[_query]
            merge_evidence_text = [f"Text: {snippet} \n Source: {_url}" for snippet, _url in zip(_snippet_list, url_to_check)]
            merge_evidence_text = [re.sub(r"\n+", "\n", evidence) for evidence in merge_evidence_text]
            evidences[_query_index] = {
                "text": "\n\n".join(merge_evidence_text),
                "url": "Multiple",
            }

        return evidences

    def _request_serper_api(self, questions):
        """Request the serper api

        Args:
            questions (list): a list of questions to request the serper api.

        Returns:
            web response: the response from the serper api
        """
        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": self.serper_key,
            "Content-Type": "application/json",
        }

        questions_data = [{"q": question, "autocorrect": False} for question in questions]
        payload = json.dumps(questions_data)
        response = None
        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            return response
        elif response.status_code == 403:
            raise Exception("Failed to authenticate. Check your API key.")
        else:
            raise Exception(f"Error occurred: {response.text}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--serper_api_key", type=str, help="API key for serper")
    args = parser.parse_args()

    api_config = {"SERPER_API_KEY": args.serper_api_key}
    retriever = SerperEvidenceRetriever(api_config)

    result = retriever._request_serper_api(["Apple", "IBM"])
    print(result.json())
