from .providers import QdrantDBProvider
from .VectorDBEnums import VectorDBEnums
from controllers.BaseController import BaseController

class VectorDBProviderFactory:

    def __init__(self, config: dict):
        self.config = config
        self.base_controller = BaseController()
    
    def create(self, provider: str):

        if provider == VectorDBEnums.QDRANT.value:
            qdrant_db_client = self.base_controller.get_database_path(db_name = self.config.QDRANT_DB_PATH)
            qdrant_cache = self.base_controller.get_cache_path(cache_name = self.config.QDRANT_CACHE_PATH)

            return QdrantDBProvider(
                db_client = qdrant_db_client,
                qdrant_cache = qdrant_cache,
                distance_method = self.config.VECTOR_DB_DISTANCE_METHOD
            )