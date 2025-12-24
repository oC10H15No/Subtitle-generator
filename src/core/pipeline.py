import os
import time
from typing import List, Tuple

from ..config.settings import AppConfig
from ..translation.factory import TranslatorFactory
from ..utils.formatter import FORMATTERS
from .engine import WhisperEngine
from .chunked_asr import ChunkedASR

class SubtitlePipeline:
    def __init__(self, config: AppConfig):
        self.config = config
        self.engine = WhisperEngine(config.model_name, config.device)
        # Initialize ChunkedASR wrapper
        self.chunked_asr = ChunkedASR(self.engine)
        self.translator = TranslatorFactory.create_translator(config.translation)

    def run(self, filename: str, output: str = None, subtitle_format: str = 'srt'):
        print(f"Start generating subtitles for {filename}...")
        start_time = time.time()

        # Transcribe (using ChunkedASR for safety with long files)
        result = self.chunked_asr.transcribe(filename, self.config.language)
        
        # Use Whisper's original segments
        segments = result['segments']
        
        transcripts = []
        regions = []
        
        # Pre-process segments
        processed_segments = []
        texts_to_translate = []

        for segment in segments:
            text = segment["text"]
            start = segment["start"]
            end = segment["end"]
            
            processed_segments.append({
                "start": start,
                "end": end,
                "original_text": text,
                "speaker_label": ""
            })
            texts_to_translate.append(text)

        # 2. Batch Translate if enabled
        translated_texts = []
        if self.translator:
            print(f"Translating {len(texts_to_translate)} segments in parallel...")
            translated_texts = self.translator.translate_batch(texts_to_translate, self.config.translation.target_language)

        # 3. Combine and Format
        for i, seg in enumerate(processed_segments):
            start = seg["start"]
            end = seg["end"]
            text = seg["original_text"]
            speaker = seg["speaker_label"]
            
            if self.translator and i < len(translated_texts):
                translated_text = translated_texts[i]
                if self.config.translation.bilingual:
                    # Bilingual format: Translated \n Original
                    # Add speaker label to both or just one? Usually just the first line or both.
                    # Let's add to the first line (Translated)
                    text = f"{speaker}{translated_text}\n{text}"
                else:
                    text = f"{speaker}{translated_text}"
            else:
                text = f"{speaker}{text}"

            regions.append((start, end))
            transcripts.append(text)

        timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t]
        
        # Format output
        formatter = FORMATTERS.get(subtitle_format)
        if not formatter:
            print(f"Warning: Format {subtitle_format} not supported, using srt.")
            formatter = FORMATTERS['srt']
            
        formatted_subtitles = formatter(subtitles=timed_subtitles)
        
        # Determine output filename
        dest = output
        if not dest:
            base = os.path.splitext(filename)[0]
            dest = "{base}.{format}".format(base=base, format=subtitle_format)

        # Write to file
        with open(dest, 'wb') as output_file:
            output_file.write(formatted_subtitles.encode("utf-8"))
            
        elapse = time.time() - start_time
        print(f"Subtitle generated at: {dest}")
        print(f"Total time: {elapse:.2f}s")


