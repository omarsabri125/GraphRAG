import logging
from fastapi.responses import JSONResponse
from controllers import NLPController
from schemes.NLP import SearchRequest
from models import ResponseEnumeration
from fastapi import APIRouter, Request

nlp_router = APIRouter(
    prefix="/api/v1",
    tags=["graph-rag"]
)

logger = logging.getLogger("uvicorn.error")

@nlp_router.get("/index/info")
async def get_project_index_info(request: Request):

    nlp_controller = NLPController(
        vector_db_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        template_parser=request.app.template_parser,
        neo4j_model=request.app.neo4j_model
    )

    collection_info = await nlp_controller.get_vector_db_collection_info()

    return JSONResponse(
        status_code=200,
        content={
            "signal": ResponseEnumeration.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": collection_info
        }
    )

@nlp_router.post("/index/search")
async def search_index(request: Request, search_request: SearchRequest):

    nlp_controller = NLPController(
        vector_db_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        template_parser=request.app.template_parser,
        neo4j_model=request.app.neo4j_model
    )

    results = await nlp_controller.search_vector_db_collection(
        query=search_request.text,
        limit=search_request.limit
    )

    if not results:
        return JSONResponse(
            status_code=400,
            content={
                "signal": ResponseEnumeration.VECTORDB_SEARCH_ERROR.value
            }
        )

    return JSONResponse(
        status_code=200,
        content={
            "signal": ResponseEnumeration.VECTORDB_SEARCH_SUCCESS.value,
            "results": [result.dict() for result in results]
        }
    )

@nlp_router.post("/index/answer")
async def answer_rag(request: Request, search_request: SearchRequest):

    nlp_controller = NLPController(
        vector_db_client=request.app.vectordb_client,
        embedding_client=request.app.embedding_client,
        generation_client=request.app.generation_client,
        template_parser=request.app.template_parser,
        neo4j_model=request.app.neo4j_model
    )

    query_vector = await nlp_controller.query_embeddings(
        text=search_request.text
    )

    # Retrieve answer from cache if exists
    cache_answer = await nlp_controller.retrieve_answer_from_cache(query_vector=query_vector)

    if cache_answer:
        return JSONResponse(
            status_code=200,
            content={
                "signal": ResponseEnumeration.CACHE_ANSWER_SUCCESS.value,
                "answer_from_cache": cache_answer
            }
        )

    answer, full_prompt, chat_history = await nlp_controller.rag_answer_question(
        query=search_request.text,
        limit=search_request.limit
    )

    if not answer:
        return JSONResponse(
            status_code=400,
            content={
                "signal": ResponseEnumeration.RAG_ANSWER_ERROR.value
            }
        )
    
    _ = await nlp_controller.add_answer_into_cache(
        query_vector=query_vector,
        answer=answer
    )

    return JSONResponse(
        status_code=200,
        content={
            "signal": ResponseEnumeration.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history

        }
    )
