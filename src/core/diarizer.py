import torch
from typing import List, Dict, Any
import os
import tempfile
from pydub import AudioSegment

class SpeakerDiarizer:
    def __init__(self, hf_token: str, device: str = 'auto'):
        self.hf_token = hf_token
        self.device = self._get_device(device)
        self.pipeline = None

    def _get_device(self, device: str) -> torch.device:
        if device == 'auto':
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device(device)

    def load_pipeline(self):
        if self.pipeline is not None:
            return

        print(f"Loading Pyannote Diarization pipeline on {self.device}...")
        try:
            from pyannote.audio import Pipeline
            # Note: use_auth_token is deprecated in newer huggingface_hub but required for older pyannote versions
            # or specific combinations. The user's environment seems to work with use_auth_token.
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
            if self.pipeline is None:
                 raise ValueError("Failed to load pipeline. Check your HF Token.")
            
            self.pipeline.to(self.device)
        except ImportError:
            print("Error: pyannote-audio not installed.")
            raise
        except Exception as e:
            print(f"Error loading diarization pipeline: {e}")
            raise

    def diarize(self, audio_path: str) -> List[Dict[str, Any]]:
        if self.pipeline is None:
            self.load_pipeline()

        print("Running speaker diarization...")
        try:
            # pyannote expects a file path
            diarization = self.pipeline(audio_path)
            
            results = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                results.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
            
            return results
        except Exception as e:
            print(f"Diarization failed: {e}")
            return []
