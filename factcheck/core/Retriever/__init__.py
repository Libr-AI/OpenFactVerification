from .GoogleEvidenceRetrieve import GoogleEvidenceRetrieve
from .SerperEvidenceRetrieve import SerperEvidenceRetrieve

retriever_map = {
    "google": GoogleEvidenceRetrieve,
    "serper": SerperEvidenceRetrieve,
}


def retriever_mapper(retriever_name: str):
    if retriever_name not in retriever_map:
        raise NotImplementedError(f"Retriever {retriever_name} not found!")
    return retriever_map[retriever_name]
