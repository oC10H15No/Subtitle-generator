from typing import Optional
from ..config.settings import TranslationConfig
from .base import BaseTranslator
from .providers import GoogleTranslator, DeepLTranslator, LLMTranslator

class TranslatorFactory:
    @staticmethod
    def create_translator(config: TranslationConfig) -> Optional[BaseTranslator]:
        if not config.enabled:
            return None
            
        provider = config.provider.lower()
        
        if provider == 'google':
            return GoogleTranslator()
        elif provider == 'deepl':
            return DeepLTranslator(config.api_key)
        elif provider == 'llm':
            return LLMTranslator(
                config.api_url,
                config.model,
                config.api_key
            )
        else:
            print(f"Unknown translator provider: {provider}, falling back to Google")
            return GoogleTranslator()
