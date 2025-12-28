from .BaseController import BaseController
from langchain_community.document_loaders import TextLoader
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.llm.LLMEnums import LLMEnums, CohereEnums
from stores.llm.templates.template_parser import TemplateParser
import uuid

class ProcessController(BaseController):

    def __init__(self):
        super().__init__()

    def load_txt_file(self, file_path: str):

        file_path = self.get_file_path(file_path)
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        return documents
    
    def sentence_splitting(self, raw_text: str):

        sentences = [sentence.strip() for sentence in raw_text.split("\n") if sentence.strip()]

        return sentences

    def extract_entity_relationship(self, text: str):

        nodes = {}
        relationships = []

        template_parser = TemplateParser(
            language=self.config.PRIMARY_LANG
        )
        llm_provider_factory = LLMProviderFactory(self.config)
        generation_client = llm_provider_factory.create_provider(
            provider_name=self.config.STRUCTURE_OUTPUT_BACKEND
        )
        generation_client.set_generation_model(model_id=self.config.GENERATION_STRUCTURE_OUTPUT_MODEL_ID)

        chat_history = template_parser.get(
            "rag", "entity_relationship_system_prompt"
        )

        user_prompt = template_parser.get(
            "rag", "entity_relationship_user_prompt", {
                "raw_data": text
            }
        )

        if self.config.STRUCTURE_OUTPUT_BACKEND == LLMEnums.COHERE.value:
            chat_history = [
                generation_client.construt_prompt(
                    prompt=chat_history,
                    role=CohereEnums.SYSTEM.value
                )
            ]

        result = generation_client.generate_with_structured_output(
            prompt=user_prompt,
            chat_history=chat_history
        )

        if not result or not hasattr(result, "graph"):
            self.logger.error("No valid graph returned from LLM")
            return {}, []

        parsed_reponse = result.graph

        for entry in parsed_reponse:
            node = entry.node
            target_node = entry.target_node
            relationship = entry.relationship

            if node and node not in nodes:
                nodes[node] = str(uuid.uuid4())

            if target_node and target_node not in nodes:
                nodes[target_node] = str(uuid.uuid4())

            if target_node and relationship:
                relationships.append(
                    {
                        "source": nodes[node],
                        "target": nodes[target_node],
                        "relationship": relationship
                    }
                )

        return nodes, relationships
    