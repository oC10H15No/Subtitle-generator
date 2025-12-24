from deep_translator import GoogleTranslator as DeepGoogleTranslator
from deep_translator import DeeplTranslator
import requests
from typing import List
from .base import BaseTranslator

class GoogleTranslator(BaseTranslator):
    def translate(self, text: str, target_lang: str) -> str:
        try:
            # deep-translator uses 'zh-CN' format usually
            if target_lang.lower() in ['zh', 'zh-cn']:
                target_lang = 'zh-CN'
            return DeepGoogleTranslator(source='auto', target=target_lang).translate(text)
        except Exception as e:
            print(f"Google Translation Error: {e}")
            return text

class DeepLTranslator(BaseTranslator):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def translate(self, text: str, target_lang: str) -> str:
        try:
            return DeeplTranslator(api_key=self.api_key, source='auto', target=target_lang).translate(text)
        except Exception as e:
            print(f"DeepL Translation Error: {e}")
            return text

class LLMTranslator(BaseTranslator):
    def __init__(self, api_url: str, model: str, api_key: str = ""):
        self.api_url = api_url
        self.model = model
        self.api_key = api_key

    def translate(self, text: str, target_lang: str) -> str:
        # Simple OpenAI compatible API implementation
        return self.translate_batch([text], target_lang)[0]

    def translate_batch(self, texts: List[str], target_lang: str, max_workers: int = 5) -> List[str]:
        """
        Translate a batch of texts using LLM with context.
        """
        if not texts:
            return []

        # Split into smaller chunks to avoid token limits
        # 20 lines per chunk is a safe bet for subtitles
        chunk_size = 20
        all_translated = []

        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            # Format: [0] Hello\n[1] World
            input_text = "\n".join([f"[{idx}] {text}" for idx, text in enumerate(chunk)])
            
            system_prompt = (
                f"You are a professional subtitle translator. "
                f"Translate the following subtitle lines into {target_lang}. "
                f"Rules:\n"
                f"1. Maintain the '[index] ' prefix for each line.\n"
                f"2. Translate each line INDIVIDUALLY. Do NOT merge lines.\n"
                f"3. If a line is a sentence fragment, translate it as a fragment.\n"
                f"4. Return exactly {len(chunk)} lines.\n"
                f"5. Do not output any explanations."
            )

            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_text}
                ],
                "temperature": 0.1
            }
            
            try:
                response = requests.post(self.api_url, headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }, json=data)
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Parse the output
                chunk_results = {}
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('[') and ']' in line:
                        try:
                            idx_str = line[1:line.index(']')]
                            text_content = line[line.index(']')+1:].strip()
                            chunk_results[int(idx_str)] = text_content
                        except ValueError:
                            continue
                
                # Fill in missing translations with original text
                for idx in range(len(chunk)):
                    all_translated.append(chunk_results.get(idx, chunk[idx]))
                    
            except Exception as e:
                print(f"LLM Batch Translation Error: {e}")
                # Fallback to original text on error
                all_translated.extend(chunk)
                
        return all_translated
