import asyncio
from controllers import NLPController, ProcessController
from helpers import get_settings, Settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from models.Neo4jModel import Neo4jModel
from neo4j import AsyncGraphDatabase

class Pipline:

    def __init__(self):

        self.settings: Settings = get_settings()

        self.db_client = AsyncGraphDatabase.driver(
            self.settings.NEO4J_URI,
            auth=(self.settings.NEO4J_USERNAME, self.settings.NEO4J_PASSWORD)
        )

        llm_provider_factory = LLMProviderFactory(self.settings)
        vectordb_provider_factory = VectorDBProviderFactory(self.settings)

        self.neo4j_model =None

        self.generation_client = llm_provider_factory.create_provider(
            self.settings.GENERATION_BACKEND)
        self.generation_client.set_generation_model(self.settings.GENERATION_MODEL_ID)

        self.embedding_client = llm_provider_factory.create_provider(
            self.settings.EMBEDDING_BACKEND)
        self.embedding_client.set_embedding_model(
            self.settings.EMBEDDING_MODEL_ID, self.settings.EMBEDDING_MODEL_DIMENSION)

        self.vectordb_client = vectordb_provider_factory.create(
            self.settings.VECTOR_DB_BACKEND)

        self.template_parser = TemplateParser(
            language=self.settings.PRIMARY_LANG,
            default_language=self.settings.DEFAULT_LANG
        )
        self.process_controller = ProcessController()
        self.nlp_controller = None

    async def pipline_indexing(self):

        await self.vectordb_client.connect()
        await self.vectordb_client.cache_connect()
        self.neo4j_model = await Neo4jModel.create_instance(self.db_client)

        self.nlp_controller = NLPController(
            self.vectordb_client,
            self.embedding_client,
            self.generation_client,
            self.template_parser,
            self.neo4j_model
        )

        documents = self.process_controller.load_txt_file(
            file_path="desiease.txt"
        )

        sentences = self.process_controller.sentence_splitting(raw_text=documents[0].page_content)

        node_id_mapping = await self.neo4j_model.retrieve_nodes_with_id()

        _ = await self.nlp_controller.index_into_vector_db(sentences, node_id_mapping)
        
        return node_id_mapping
    

async def main():
    pip = Pipline()
    node_id_mapping = await pip.pipline_indexing()
    print(node_id_mapping)

asyncio.run(main())







