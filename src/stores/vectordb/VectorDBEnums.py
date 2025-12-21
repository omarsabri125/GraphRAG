from enum import Enum

class VectorDBEnums(Enum):
    QDRANT = "qdrant"
    MILVUS = "milvus"


class DistanceMetricEnums(Enum):
    COSINE = "cosine"
    EUCLIDEAN = "euclid"
    DOT_PRODUCT = "dot"

class QdrantVectorType(Enum):
    DENSE = "dense"
    SPARSE = "sparse"


