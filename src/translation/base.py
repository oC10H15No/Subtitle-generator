import abc
from typing import List
from concurrent.futures import ThreadPoolExecutor

class BaseTranslator(abc.ABC):
    @abc.abstractmethod
    def translate(self, text: str, target_lang: str) -> str:
        pass

    def translate_batch(self, texts: List[str], target_lang: str, max_workers: int = 5) -> List[str]:
        """
        Default implementation of batch translation using threads.
        Subclasses can override this for optimized batch APIs.
        """
        if not texts:
            return []
            
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map preserves order
            results = list(executor.map(lambda t: self.translate(t, target_lang), texts))
        return results
