from concurrent.futures import ThreadPoolExecutor
from factcheck.utils.web_util import common_web_request, crawl_google_web
from .base import BaseRetriever
from factcheck.utils.logger import CustomLogger

logger = CustomLogger(__name__).getlog()


class GoogleEvidenceRetriever(BaseRetriever):
    def __init__(self, api_config: dict = None) -> None:
        super(GoogleEvidenceRetriever, self).__init__(api_config)
        self.num_web_pages = 10

    def _get_query_urls(self, questions: list[str]):
        all_request_url_dict = dict()
        for query in questions:
            query = query.replace(" ", "+")
            curr_query_list = all_request_url_dict.get(query, [])
            for page in range(0, self.num_web_pages, 10):
                # here page is google search's bottom page meaning, click 2 -> start=10
                # url = "https://www.google.com/search?q={}&start={}".format(query, page)
                url = "https://www.google.com/search?q={}&lr=lang_{}&hl={}&start={}".format(query, self.lang, self.lang, page)
                curr_query_list.append(url)
                all_request_url_dict[query] = curr_query_list

        crawled_all_page_urls_dict = dict()
        with ThreadPoolExecutor(max_workers=len(all_request_url_dict.values())) as executor:
            futures = list()
            for query, urls in all_request_url_dict.items():
                for url in urls:
                    future = executor.submit(common_web_request, url, query)
                    futures.append(future)
            for future in futures:
                response, query = future.result()
                content_list = crawled_all_page_urls_dict.get(query, [])
                content_list.extend(crawl_google_web(response))
                crawled_all_page_urls_dict[query] = content_list
        for query, urls in crawled_all_page_urls_dict.items():
            # urls = sorted(list(set(urls)))
            crawled_all_page_urls_dict[query] = urls[: self.max_search_result_per_query]
        return crawled_all_page_urls_dict
