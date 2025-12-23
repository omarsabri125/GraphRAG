from .BaseController import BaseController
from stores.llm.LLMEnums import DocumentTypeEnum
import json 

class NLPController(BaseController):

    def __init__(self, vector_db_client, embedding_client, generation_client, template_parser):
        super().__init__()
        self.vector_db_client = vector_db_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client
        self.template_parser = template_parser
    
    async def reset_vector_db_collection(self):
        return await self.vector_db_client.delete_collection(collection_name=self.config.COLLECTION_NAME)
    
    async def reset_cache_vector_db_collection(self):
        return await self.vector_db_client.delete_cache_collection(collection_name=self.config.CACHE_NAME)
    
    async def get_vector_db_collection_info(self):

        collection_info = await self.vector_db_client.get_collection_info(collection_name=self.config.COLLECTION_NAME)
        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )
    
    async def index_into_vector_db(self, sentences: list, node_id_mapping: dict, do_reset: bool = False, batch_size: int = 50):

        embeddings = []
        entity_ids = []

        for i in range(0, len(sentences), batch_size):

            batch_sentences = sentences[i:i + batch_size]

            batch_entity_ids = []
            for sentence in batch_sentences:
                entities_in_sentence = [
                    node_id for entity, node_id in node_id_mapping.items() 
                    if entity in sentence
                ]
                batch_entity_ids.append(entities_in_sentence)

            batch_embeddings = self.embedding_client.embed_text(
                texts=batch_sentences, document_type=DocumentTypeEnum.DOCUMENT.value
            )

            embeddings.extend(batch_embeddings)
            entity_ids.extend(batch_entity_ids)

        _ = await self.vector_db_client.create_collection(
            collection_name=self.config.COLLECTION_NAME,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
        )

        _ = await self.vector_db_client.insert_many(
            collection_name=self.config.COLLECTION_NAME,
            texts=sentences,
            vectors=embeddings,
            entity_ids=entity_ids
        )
    
    async def query_embeddings(self, text: str):
        
        vectors = self.embedding_client.embed_text(
            text, DocumentTypeEnum.QUERY.value)

        if not vectors or len(vectors) == 0:
            return False

        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0]

        if not query_vector:
            return False
        
        return query_vector
    
    async def retrieve_answer_from_cache(self, query_vector: list, cache_threshold=0.7):

        cache_result = await self.vector_db_client.search_cache(
            cache_name=self.config.CACHE_NAME,
            vector=query_vector
        )
        if cache_result:
            for s in cache_result:
                if s.score <= cache_threshold:
                    return s.payload["response_text"]
    
    async def add_answer_into_cache(self, query_vector: list, answer: str):

        _ = await self.vector_db_client.add_to_cache(
            cache_name=self.config.CACHE_NAME,
            vector=query_vector,
            response_text=answer
        )
        return True
