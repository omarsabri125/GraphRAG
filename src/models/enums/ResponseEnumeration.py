from enum import Enum
class ResponseEnumeration(Enum):
    VECTORDB_COLLECTION_RETRIEVED = "vectordb_collection_retrieved"
    VECTORDB_SEARCH_ERROR = "vectordb_search_error"
    VECTORDB_SEARCH_SUCCESS = "vectordb_search_success"
    RAG_ANSWER_ERROR = "rag_answer_error"
    RAG_ANSWER_SUCCESS = "rag_answer_success"
    CACHE_ANSWER_ERROR = "cache_answer_error"
    CACHE_ANSWER_SUCCESS = "cache_answer_success"