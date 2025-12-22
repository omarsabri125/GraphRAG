from .LLMEnums import LLMEnums
from .providers import CohereProvider, GeminiProvider

class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config

    def create_provider(self, provider_name: str):

        if provider_name == LLMEnums.COHERE.value:

            return CohereProvider(
                api_key=self.config.COHERE_API_KEY,
                default_output_max_tokens=self.config.DAFAULT_OUTPUT_MAX_TOKENS,
                default_temperature=self.config.DAFAULT_TEMPERATURE
            )
        
        if provider_name == LLMEnums.GEMINI.value:

            return GeminiProvider(
                api_key=self.config.GEMINI_API_KEY,
                default_output_max_tokens=self.config.DAFAULT_OUTPUT_MAX_TOKENS,
                default_temperature=self.config.DAFAULT_TEMPERATURE
            )
        
        return None