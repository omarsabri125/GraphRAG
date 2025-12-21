from ..LLMInterface import LLMInterface
from ..LLMEnums import GeminiEnums, DocumentTypeEnum
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig
import logging

class GeminiProvider(LLMInterface):

    def __init__(self, api_key: str, 
                   default_output_max_tokens: int = 200,
                   default_temperature: float = 0.1):
        
        self.api_key = api_key
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temperature = default_temperature
        
        self.embedding_model_id = None
        self.embedding_size = None

        self.generation_model_id = None

        self.client = genai.Client(api_key= self.api_key)

        self.enums = GeminiEnums
        self.logger = logging.getLogger(__name__)

    def set_embedding_model(self, model_id: str, embedding_dimension: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_dimension
    
    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def embed_text(self, text: str, document_type = None):

        if not self.client:
            self.logger.error("Gemini client was not set")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding Model ID was not set")
            return None

        input_type = self.enums.DOCUMENT.value
        if document_type == DocumentTypeEnum.QUERY.value:
            input_type = self.enums.QUERY.value
        
        if isinstance(text, str):
            text = [text]
        
        embeddings_result = self.client.models.embed_content(
            model = self.embedding_model_id,
            contents = text,
            config=types.EmbedContentConfig(output_dimensionality=self.embedding_size,
                                            task_type=input_type)
        )

        if not embeddings_result or not embeddings_result.embeddings:
            self.logger.error("No embedding returned from Gemini.")
            return None

        return [embed for embed in embeddings_result.embeddings]
    
    def generate_text(self, prompt, chat_history= [], max_output_tokens = None, temperature = None):
        
        if not self.client:
            self.logger.error("Gemini client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation Model ID was not set")
            return None
        
        
        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.default_output_max_tokens
        temperature = temperature if temperature is not None else self.default_temperature
        
        response = self.client.models.generate_content(
            model = self.generation_model_id,
            contents= prompt,
            config=GenerateContentConfig(
                system_instruction = chat_history,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
        )

        if not response or not response.text:
            return None
        
        return response.text

    def construt_prompt(self, prompt, role):
        raise NotImplementedError  
    









