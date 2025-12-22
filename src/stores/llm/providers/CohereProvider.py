from ..LLMInterface import LLMInterface
from ..LLMEnums import CohereEnums, DocumentTypeEnum
from typing import Union, List
from schemes.GraphComponents import GraphComponents
import logging
import cohere

class CohereProvider(LLMInterface):

    def __init__(self, api_key: str,
                 default_output_max_tokens: int = 1000,
                 default_temperature: float = 0.1):
        
        self.api_key = api_key
        
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.enums = CohereEnums

        self.client = cohere.ClientV2(api_key=self.api_key)

        self.logger = logging.getLogger(__name__)
    
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str, embedding_dimension: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_dimension
    
    def generate_with_structured_output(self, prompt: str, chat_history=[]):
        
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model is not set.")
            return None
        
        
        chat_history.append(
            self.construt_prompt(prompt, role=CohereEnums.USER.value)
        )

        response = self.client.chat(
            model=self.generation_model_id,
            messages=chat_history,
            response_format={"type": "json_object"},
        )

        if not response or not response.message.content[0].text:
            self.logger.error("No response from Cohere API.")
            return None
        
        text = response.message.content[0].text
        
        return GraphComponents.model_validate_json(text)

    def generate_text(self, prompt: str, chat_history=[], max_output_tokens: int = None, temperature: float = None):
        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None

        if not self.generation_model_id:
            self.logger.error("Generation model is not set.")
            return None

        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.default_output_max_tokens
        temperature = temperature if temperature is not None else self.default_temperature

        chat_history.append(
            self.construt_prompt(prompt, role=CohereEnums.USER.value)
        )

        response = self.client.chat(
            model=self.generation_model_id,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temperature
        )

        if not response or not response.message.content[0].text:
            self.logger.error("No response from Cohere API.")
            return None
        
        return response.message.content[0].text
    
    def embed_text(self, text: Union[str, List[str]], document_type: str = None):

        if not self.client:
            self.logger.error("Cohere client is not initialized.")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model is not set.")
            return None
        
        input_type = CohereEnums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = CohereEnums.QUERY.value

        if isinstance(text, str):
            text = [text]
        
        res = self.client.embed(
            model = self.embedding_model_id,
            texts = text,
            input_type = input_type,
            embedding_types=["float"],
        )

        if not res or not res.embeddings.float:
            self.logger.error("No embedding returned from Cohere.")
            return None
        
        
        return [ f for f in res.embeddings.float ]


    def construt_prompt(self, prompt: str, role: str):

        return {
            "role": role,
            "content": prompt
        }