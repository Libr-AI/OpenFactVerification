from .google_retriever import GoogleEvidenceRetriever
from .serper_retriever import SerperEvidenceRetriever

retriever_map = {
    "google": GoogleEvidenceRetriever,
    "serper": SerperEvidenceRetriever,
}


def retriever_mapper(retriever_name: str):
    if retriever_name not in retriever_map:
        raise NotImplementedError(f"Retriever {retriever_name} not found!")
    return retriever_map[retriever_name]
