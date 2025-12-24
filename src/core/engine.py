import whisper
import torch
from typing import Dict, Any

class WhisperEngine:
    def __init__(self, model_name: str, device: str = 'auto'):
        self.model_name = model_name
        self.device = self._get_device(device)
        self.model = None

    def _get_device(self, device: str) -> str:
        if device == 'auto':
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def load_model(self):
        print(f"Loading openai-whisper model {self.model_name} on {self.device}...")
        try:
            self.model = whisper.load_model(self.model_name, device=self.device)
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to CPU...")
            self.device = "cpu"
            self.model = whisper.load_model(self.model_name, device="cpu")

    def transcribe(self, audio_path: str, language: str = 'auto') -> Dict[str, Any]:
        if not self.model:
            self.load_model()

        lang_arg = None
        if language != 'auto':
            if language.lower() in ('zh-cn', 'zh-tw', 'zh-hk', 'zh-sg', 'zh-hans', 'zh-hant'):
                lang_arg = "zh"
            else:
                lang_arg = language
        
        print("Transcribing...")
        
        # openai-whisper transcribe options
        options = {
            "word_timestamps": True
        }
        if lang_arg:
            options["language"] = lang_arg

        result = self.model.transcribe(audio_path, **options)
        
        for segment in result.get("segments", []):
            print(f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")

        return result
