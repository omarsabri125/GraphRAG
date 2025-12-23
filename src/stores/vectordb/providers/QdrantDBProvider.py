from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMetricEnums, QdrantVectorType
from qdrant_client import QdrantClient, models
import uuid
import logging
from typing import List

class QdrantDBProvider(VectorDBInterface):

    def __init__(self, db_client: str, qdrant_cache:str, distance_method: str, cache_threshold=0.35):

        self.client = None
        self.cache_client = None
        self.db_client = db_client
        self.qdrant_cache = qdrant_cache
        self.distance_method = None
        self.modifier = models.Modifier.IDF
        self.cache_threshold = cache_threshold

        if distance_method == DistanceMetricEnums.COSINE.value:
            self.distance_method = models.Distance.COSINE
        elif distance_method == DistanceMetricEnums.EUCLIDEAN.value:
            self.distance_method = models.Distance.EUCLID
        elif distance_method == DistanceMetricEnums.DOT_PRODUCT.value:
            self.distance_method = models.Distance.DOT

        self.logger = logging.getLogger(__name__)

    async def cache_connect(self):
        self.cache_client = QdrantClient(path=self.qdrant_cache)
    
    async def cache_disconnect(self):
        self.cache_client = None
    
    async def is_cache_collection_exists(self, cache_name: str) -> bool:
        return self.cache_client.collection_exists(collection_name=cache_name)
    
    async def delete_cache_collection(self, cache_name: str) -> bool:
        if await self.is_cache_collection_exists(cache_name):
            self.cache_client.delete_collection(collection_name=cache_name)
            return True
        return False
    
    async def create_cache_collection(self, cache_name: str, embedding_size: int, do_reset: bool = False):

        if do_reset:
            _ = await self.delete_cache_collection(cache_name)

        if not await self.is_cache_collection_exists(cache_name):
            self.logger.info(
                f"Creating new Qdrant cache collection: {cache_name}")
    
            self.cache_client.create_collection(
                collection_name=cache_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=models.Distance.EUCLID
                )
            )

    async def search_cache(self, cache_name: str, vector: list):

        search_result = self.cache_client.search(
            collection_name=cache_name,
            query_vector=vector,
            limit=1
        )
        return search_result
    
    async def add_to_cache(self, cache_name: str, vector: list, response_text: str):

        point_id = str(uuid.uuid4())
        point = models.PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "response_text": response_text
            }
        )
        try:
            self.cache_client.upsert(
                collection_name=cache_name,
                points=[point]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting cache: {e}")
            return False
         
        return True
    
    async def connect(self):
        self.client = QdrantClient(path=self.db_client)

    async def disconnect(self):
        self.client = None

    async def is_collection_exists(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)

    async def list_all_collections(self):
        return self.client.get_collections()

    async def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name=collection_name)

    async def delete_collection(self, collection_name: str) -> bool:
        if await self.is_collection_exists(collection_name):
            self.client.delete_collection(collection_name=collection_name)
            return True
        return False

    async def create_collection(self, collection_name: str, embedding_size: int, do_reset: bool = False):

        if do_reset:
            _ = await self.delete_collection(collection_name)

        if not await self.is_collection_exists(collection_name):
            self.logger.info(
                f"Creating new Qdrant collection: {collection_name}")

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    QdrantVectorType.DENSE.value: models.VectorParams(
                        size=embedding_size,
                        distance=self.distance_method
                    ),
                },
                sparse_vectors_config={
                    QdrantVectorType.SPARSE.value: models.SparseVectorParams(
                        modifier=self.modifier
                    )
                }
            )

            return True

        return False

    async def insert_one(self, collection_name: str, text: str, vector: list, entity_ids: list = None):

        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        point = models.PointStruct(
            id=id,
            vector=vector,
            payload={
                "text": text,
                "entity_id": entity_ids
            }
        )

        self.client.upsert(
            collection_name=collection_name,
            points=[point]
        )

        return True

    async def insert_many(self, collection_name: str, texts: list, vectors: list, entity_ids: list = None, batch_size: int = 50):

        if not await self.is_collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} does not exist.")
            return False

        for start_idx in range(0, len(texts), batch_size):

            batch_text = texts[start_idx: start_idx + batch_size]
            batch_vectors = vectors[start_idx: start_idx + batch_size]
            batch_entity_ids = entity_ids[start_idx: start_idx + batch_size]

            batch_points = [
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector={
                        QdrantVectorType.DENSE.value: batch_vectors[x],
                        QdrantVectorType.SPARSE.value: models.Document(
                            text=batch_text[x],
                            model="Qdrant/bm25",
                        ),
                    },
                    payload={
                        "text": batch_text[x],
                        "entity_ids": batch_entity_ids[x]
                    }
                )
                for x in range(len(batch_text))
            ]

            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )

            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True

    async def search_by_vector(self, collection_name: str, text: str, query_vector: List, limit: int):

        results = self.client.query_points(
            collection_name=collection_name,
            prefetch=[
                models.Prefetch(
                    query=query_vector,
                    using=QdrantVectorType.DENSE.value,
                    limit=limit,
                ),
                models.Prefetch(
                    query=models.Document(
                        text=text,
                        model="Qdrant/bm25",
                    ),
                    using=QdrantVectorType.SPARSE.value,
                    limit=limit,
                )
            ],
            query=models.FusionQuery(
                fusion=models.Fusion.DBSF
            ),
            limit=limit
        )

        results = [
            {
                "score": res.score,
                "text": res.payload["text"],
                "entity_ids": res.payload["entity_ids"]
            }
            for res in results.points
        ]

        return results
