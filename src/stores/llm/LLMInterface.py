from abc import ABC, abstractmethod
from typing import Union, List
class LLMInterface(ABC):

     @abstractmethod
     def set_embedding_model(self, model_id: str, embedding_dimension: int):
          pass
     
     @abstractmethod
     def set_generation_model(self, model_id: str):
          pass

     @abstractmethod
     def generate_with_structured_output(self, prompt: str, chat_history=[]):
          pass
     
     @abstractmethod
     def generate_text(self, prompt: str, chat_history=[], max_output_tokens: int = None, temperature: float = None):
          pass
     
     @abstractmethod
     def embed_text(self, text: Union[str, List[str]], document_type: str = None):
          pass
     @abstractmethod
     def construt_prompt(self, prompt: str, role: str):
          pass

