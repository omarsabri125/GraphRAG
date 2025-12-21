from enum import Enum

class LLMEnums(Enum):
    GEMINI = "GEMINI"
    COHERE = "COHERE"

class CohereEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    DOCUMENT = "search_document"
    QUERY = "search_query"

class GeminiEnums(Enum):
    DOCUMENT = "RETRIEVAL_DOCUMENT"
    QUERY = "RETRIEVAL_QUERY"


class DocumentTypeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"
