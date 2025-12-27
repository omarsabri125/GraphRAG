import asyncio
from controllers import NLPController, ProcessController
from helpers import get_settings, Settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from models.Neo4jModel import Neo4jModel
from neo4j import AsyncGraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self):
        self.settings: Settings = get_settings()

        # Neo4j async driver
        self.db_client = AsyncGraphDatabase.driver(
            self.settings.NEO4J_URI,
            auth=(self.settings.NEO4J_USERNAME, self.settings.NEO4J_PASSWORD)
        )

        # Factories
        llm_provider_factory = LLMProviderFactory(self.settings)
        vectordb_provider_factory = VectorDBProviderFactory(self.settings)

        # Clients
        self.generation_client = llm_provider_factory.create_provider(
            self.settings.GENERATION_BACKEND
        )
        self.generation_client.set_generation_model(self.settings.GENERATION_MODEL_ID)

        self.embedding_client = llm_provider_factory.create_provider(
            self.settings.EMBEDDING_BACKEND
        )
        self.embedding_client.set_embedding_model(
            self.settings.EMBEDDING_MODEL_ID,
            self.settings.EMBEDDING_MODEL_DIMENSION
        )

        self.vectordb_client = vectordb_provider_factory.create(
            self.settings.VECTOR_DB_BACKEND
        )

        # Utilities
        self.template_parser = TemplateParser(
            language=self.settings.PRIMARY_LANG,
            default_language=self.settings.DEFAULT_LANG
        )
        self.process_controller = ProcessController()

        # Lazy init
        self.neo4j_model: Neo4jModel | None = None
        self.nlp_controller: NLPController | None = None

    async def close(self):
        """Close all async connections properly."""
        await self.vectordb_client.disconnect()
        await self.db_client.close()

    # ----------------- ENTITY EXTRACTION -----------------
    async def entity_extraction_pipeline(self, file_path: str = "desiease.txt"):
        """Load file, extract entities and relationships, ingest into Neo4j."""
        self.neo4j_model = await Neo4jModel.create_instance(self.db_client)

        documents = self.process_controller.load_txt_file(file_path)
        if not documents:
            logger.warning(f"No documents found in {file_path}")
            return [], []

        content = documents[0].page_content
        nodes, relationships = self.process_controller.extract_entity_relationship(content)

        ingested_nodes = await self.neo4j_model.ingest_to_neo4j(nodes, relationships)
        logger.info(f"Ingested {len(nodes)} nodes and {len(relationships)} relationships into Neo4j")
        return ingested_nodes

    # ----------------- VECTOR DB INDEXING -----------------
    async def pipeline_indexing(self, file_path: str = "desiease.txt"):
        """Split sentences, retrieve node IDs, and index into vector DB."""
        # Connect to VectorDB
        await self.vectordb_client.connect()
        # await self.vectordb_client.cache_connect()

        # Ensure Neo4j instance
        if self.neo4j_model is None:
            self.neo4j_model = await Neo4jModel.create_instance(self.db_client)

        # Initialize NLP controller
        self.nlp_controller = NLPController(
            vector_db_client=self.vectordb_client,
            embedding_client=self.embedding_client,
            generation_client=self.generation_client,
            template_parser=self.template_parser,
            neo4j_model=self.neo4j_model
        )

        # Load and split sentences
        documents = self.process_controller.load_txt_file(file_path)
        if not documents:
            logger.warning(f"No documents found in {file_path}")
            return {}

        sentences = self.process_controller.sentence_splitting(documents[0].page_content)
        logger.info(f"Total sentences to index: {len(sentences)}")

        # Retrieve node IDs
        node_id_mapping = await self.neo4j_model.retrieve_nodes_with_id()

        # Index sentences into vector DB
        success = await self.nlp_controller.index_into_vector_db(sentences, node_id_mapping)
        if success:
            logger.info("VectorDB indexing completed successfully")
        else:
            logger.error("VectorDB indexing failed")

        return node_id_mapping

# ----------------- MAIN -----------------
async def main():
    pipeline = Pipeline()
    try:
        # Step 1: Extract entities
        # await pipeline.entity_extraction_pipeline("desiease.txt")

        # Step 2: Index sentences into vector DB
        node_id_mapping = await pipeline.pipeline_indexing("desiease.txt")
        logger.info(f"Node ID mapping retrieved: {len(node_id_mapping)} nodes")
    finally:
        # Close all async connections
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
