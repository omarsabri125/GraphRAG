from .BaseController import BaseController
from stores.llm.LLMEnums import DocumentTypeEnum, LLMEnums
from tqdm.asyncio import tqdm
import logging
import json 

class NLPController(BaseController):

    def __init__(self, vector_db_client, embedding_client, generation_client, template_parser, neo4j_model):
        super().__init__()
        self.vector_db_client = vector_db_client
        self.embedding_client = embedding_client
        self.generation_client = generation_client
        self.template_parser = template_parser
        self.neo4j_model = neo4j_model
        self.logger = logging.getLogger(__name__)
    
    async def reset_vector_db_collection(self):
        return await self.vector_db_client.delete_collection(collection_name=self.config.COLLECTION_NAME)
    
    async def reset_cache_vector_db_collection(self):
        return await self.vector_db_client.delete_cache_collection(collection_name=self.config.CACHE_NAME)
    
    async def get_vector_db_collection_info(self):

        collection_info = await self.vector_db_client.get_collection_info(collection_name=self.config.COLLECTION_NAME)
        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )
    
    def format_graph_context(self, subgraph):
        nodes = set()
        edges = set()  

        for entry in subgraph:
            entity = entry["entity"]
            related = entry["related_node"]
            relationship = entry["relationship"]

            nodes.add(entity["name"])
            nodes.add(related["name"])

            edge = f"{entity['name']} {relationship['type']} {related['name']}"
            edges.add(edge)
            # edges.append(f"{entity['name']} {relationship['type']} {related['name']}")   

        return {
            "nodes": list(nodes),
            "edges": list(edges)
        }
    
    def extract_entity_ids(self, search_results):
        seen = dict()   

        for result in search_results:
            for _id in result.entity_ids:
                if _id not in seen:
                    seen[_id] = None

        return list(seen.keys())

    async def index_into_vector_db(self, sentences: list, node_id_mapping: dict, do_reset: bool = False, batch_size: int = 50):
        embeddings = []
        entity_ids = []
        
        # Calculate total number of batches for progress tracking
        total_batches = (len(sentences) + batch_size - 1) // batch_size
        
        # Process batches with progress bar
        for i in tqdm(range(0, len(sentences), batch_size), 
                    total=total_batches,
                    desc="Processing batches",
                    unit="batch"):
            batch_sentences = sentences[i:i + batch_size]
            batch_entity_ids = []
            
            for sentence in batch_sentences:
                entities_in_sentence = [
                    node_id for entity, node_id in node_id_mapping.items() 
                    if entity in sentence
                ]
                batch_entity_ids.append(entities_in_sentence)
            
            batch_embeddings = self.embedding_client.embed_text(
                text=batch_sentences,
                document_type=DocumentTypeEnum.DOCUMENT.value
            )
            
            embeddings.extend(batch_embeddings)
            entity_ids.extend(batch_entity_ids)
        
        # Create collection
        _ = await self.vector_db_client.create_collection(
            collection_name=self.config.COLLECTION_NAME,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
        )

        # Create semantic cache
        _ = await self.vector_db_client.create_cache_collection(
            cache_name=self.config.CACHE_NAME,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset
        )
        
        self.logger.info(f"Inserting {len(sentences)} sentences into vector database...")
        _ = await self.vector_db_client.insert_many(
            collection_name=self.config.COLLECTION_NAME,
            texts=sentences,
            vectors=embeddings,
            entity_ids=entity_ids
        )
        self.logger.info("Indexing complete!")
        
        return True
        
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
    
    async def retrieve_answer_from_cache(self, query_vector: list, cache_threshold=0.3):

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
    
    async def search_vector_db_collection(self, query: str, limit: int = 5):

        query_vector = await self.query_embeddings(text=query)

        result = await self.vector_db_client.search_by_vector(
            collection_name=self.config.COLLECTION_NAME,
            text=query,
            query_vector=query_vector,
            limit=limit
        )

        if not result:
            return False
        
        return result
    
    async def graph_rag_answer_question(self, query: str, limit: int = 5):

        answer, full_prompt, chat_history = None, None, None

        retrieved_graph_components = await self.search_vector_db_collection(query, limit)

        if not retrieved_graph_components or len(retrieved_graph_components) == 0:
            return answer, full_prompt, chat_history
        
        entity_ids = self.extract_entity_ids(retrieved_graph_components)

        subgraph = await self.neo4j_model.fetch_related_graph(entity_ids=entity_ids)
        
        graph_context = self.format_graph_context(subgraph)

        nodes_str = ", ".join(graph_context["nodes"])
        edges_str = "; ".join(graph_context["edges"])

        chat_history = self.template_parser.get("rag", "kg_system_prompt")

        graph_prompt = self.template_parser.get("rag", "kg_graph_prompt", {
            "nodes": nodes_str,
            "edges": edges_str
        })

        footer_prompt = self.template_parser.get("rag", "kg_footer_prompt", {
            "query": query
        })

        full_prompt = "\n\n".join([graph_prompt, footer_prompt])

        if self.config.GENERATION_BACKEND == LLMEnums.COHERE.value:
            chat_history = [
                self.generation_client.construt_prompt(
                    prompt=chat_history,
                    role=self.generation_client.enums.SYSTEM.value
                )
            ]

        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        return answer, full_prompt, chat_history
        


        





