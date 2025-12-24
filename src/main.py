from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.base import base_router
from routes.nlp import nlp_router
from helpers import get_settings, Settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from models.Neo4jModel import Neo4jModel
from neo4j import AsyncGraphDatabase

app = FastAPI(title="GraphRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=["*"],
    allow_headers=["*"],
)

async def startup_span():

    settings: Settings = get_settings()

    app.db_client = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )

    llm_provider_factory = LLMProviderFactory(settings)
    vectordb_provider_factory = VectorDBProviderFactory(settings)

    app.neo4j_model = await Neo4jModel.create_instance(app.db_client)

    app.generation_client = llm_provider_factory.create_provider(
        settings.GENERATION_BACKEND)
    app.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    app.embedding_client = llm_provider_factory.create_provider(
        settings.EMBEDDING_BACKEND)
    app.embedding_client.set_embedding_model(
        settings.EMBEDDING_MODEL_ID, settings.EMBEDDING_MODEL_DIMENSION)

    app.vectordb_client = vectordb_provider_factory.create(
        settings.VECTOR_DB_BACKEND)
    await app.vectordb_client.connect()
    await app.vectordb_client.cache_connect()

    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG
    )

async def shutdown_span():
    await app.db_client.close()
    await app.vectordb_client.disconnect()
    await app.vectordb_client.cache_disconnect()

app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

app.include_router(base_router)
app.include_router(nlp_router)

