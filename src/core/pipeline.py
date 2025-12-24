import os
import time
import tempfile
import subprocess
from typing import List, Tuple, Dict, Any

from ..config.settings import AppConfig
from ..translation.factory import TranslatorFactory
from ..utils.formatter import FORMATTERS
from .engine import WhisperEngine
from .chunked_asr import ChunkedASR
from .diarizer import SpeakerDiarizer

class SubtitlePipeline:
    def __init__(self, config: AppConfig):
        self.config = config
        self.engine = WhisperEngine(config.model_name, config.device)
        # Initialize ChunkedASR wrapper
        self.chunked_asr = ChunkedASR(self.engine)
        self.translator = TranslatorFactory.create_translator(config.translation)
        
        self.diarizer = None
        if config.diarization and config.diarization.enabled:
            if not config.diarization.hf_token:
                print("Warning: Diarization enabled but no HF Token provided. Disabling.")
            else:
                self.diarizer = SpeakerDiarizer(config.diarization.hf_token, config.device)

    def _assign_speakers(self, segments: List[Dict[str, Any]], diarization_result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign speaker labels to Whisper segments based on pyannote diarization results.
        
        Strategy: 
        - Keep Whisper's segment boundaries intact (Whisper already does sentence-level segmentation).
        - For each segment, find the pyannote speaker with the longest time overlap.
        - This prevents breaking natural sentence boundaries due to brief speaker jitter.
        """
        if not diarization_result:
            return segments

        # Sort diarization results by start time for efficient processing
        diarization_result = sorted(diarization_result, key=lambda x: x['start'])

        def find_best_speaker_for_segment(seg_start: float, seg_end: float) -> str:
            """
            Find the speaker whose diarization turn has the longest overlap with [seg_start, seg_end].
            
            If no overlap exists (segment falls in a diarization gap), find the nearest speaker
            within a reasonable distance (2 seconds).
            
            Returns speaker label or None.
            """
            best_speaker = None
            best_overlap_duration = 0.0

            # First pass: find speaker with maximum overlap
            for dia in diarization_result:
                overlap_start = max(seg_start, dia['start'])
                overlap_end = min(seg_end, dia['end'])
                overlap_duration = max(0.0, overlap_end - overlap_start)

                if overlap_duration > best_overlap_duration:
                    best_overlap_duration = overlap_duration
                    best_speaker = dia['speaker']

            # If we found an overlap, return that speaker
            if best_overlap_duration > 0:
                return best_speaker

            # No overlap found - segment is in a gap between diarization turns
            # Find the nearest diarization turn (by distance to segment midpoint)
            seg_midpoint = (seg_start + seg_end) / 2
            min_distance = float('inf')
            nearest_speaker = None

            for dia in diarization_result:
                # Calculate distance from segment midpoint to diarization turn
                if dia['start'] <= seg_midpoint < dia['end']:
                    # Midpoint is inside this turn (shouldn't happen if overlap was 0, but just in case)
                    return dia['speaker']
                elif seg_midpoint < dia['start']:
                    distance = dia['start'] - seg_midpoint
                else:  # seg_midpoint >= dia['end']
                    distance = seg_midpoint - dia['end']

                if distance < min_distance:
                    min_distance = distance
                    nearest_speaker = dia['speaker']

            # Only use nearest speaker if within 2 seconds
            max_gap_tolerance = 2.0
            if min_distance <= max_gap_tolerance:
                return nearest_speaker

            return None

        # Assign speaker to each Whisper segment (keep segmentation intact)
        for seg in segments:
            speaker = find_best_speaker_for_segment(seg['start'], seg['end'])
            seg['speaker_label'] = f"[{speaker}] " if speaker else ""

        return segments

    def run(self, filename: str, output: str = None, subtitle_format: str = 'srt'):
        print(f"Start generating subtitles for {filename}...")
        start_time = time.time()
        
        # Pre-process audio to a single WAV source for consistency
        temp_wav_path = None
        try:
            print("Converting audio to temporary WAV via ffmpeg for consistent processing...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_wav_path = tmp.name

            # Explicit ffmpeg conversion:
            # - mono (-ac 1)
            # - 16kHz (-ar 16000)
            # - disable video (-vn)
            # - overwrite (-y)
            cmd = [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                filename,
                "-ac",
                "1",
                "-ar",
                "16000",
                "-vn",
                temp_wav_path,
            ]
            try:
                subprocess.run(cmd, check=True)
            except FileNotFoundError as e:
                raise RuntimeError(
                    "ffmpeg not found in PATH. Please install ffmpeg and ensure it is available as `ffmpeg`."
                ) from e
            except subprocess.CalledProcessError as e:
                raise RuntimeError("ffmpeg failed to convert input to WAV. See ffmpeg output above.") from e
            
            # 1. Transcribe (using ChunkedASR for safety with long files)
            # Pass the temp wav file instead of original filename
            result = self.chunked_asr.transcribe(temp_wav_path, self.config.language)
            segments = result['segments']
            
            # 2. Diarization (Optional)
            if self.diarizer:
                print("Running Diarization...")
                # Pass the SAME temp wav file
                diarization_result = self.diarizer.diarize(temp_wav_path)
                segments = self._assign_speakers(segments, diarization_result)
        
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)
        
        transcripts = []
        regions = []
        
        # Pre-process segments for translation
        processed_segments = []
        texts_to_translate = []

        for segment in segments:
            text = segment.get("text", "")
            start = segment["start"]
            end = segment["end"]
            speaker = segment.get("speaker_label", "")

            # Drop empty/whitespace-only segments early (avoids "[SPEAKER_xx]" with no content)
            if not text or not str(text).strip():
                continue
            
            processed_segments.append({
                "start": start,
                "end": end,
                "original_text": text,
                "speaker_label": speaker
            })
            texts_to_translate.append(text)

        # 3. Batch Translate if enabled
        translated_texts = []
        if self.translator:
            print(f"Translating {len(texts_to_translate)} segments in parallel...")
            translated_texts = self.translator.translate_batch(texts_to_translate, self.config.translation.target_language)

        # 4. Combine and Format
        for i, seg in enumerate(processed_segments):
            start = seg["start"]
            end = seg["end"]
            text = seg["original_text"]
            speaker = seg["speaker_label"]
            
            if self.translator and i < len(translated_texts):
                translated_text = translated_texts[i]
                if self.config.translation.bilingual:
                    # Bilingual format: Translated \n Original
                    # Add speaker label to the first line (Translated)
                    text = f"{speaker}{translated_text}\n{text}"
                else:
                    text = f"{speaker}{translated_text}"
            else:
                text = f"{speaker}{text}"

            regions.append((start, end))
            transcripts.append(text)

        # Filter out empty subtitles after speaker/translation composition as well
        timed_subtitles = [(r, t) for r, t in zip(regions, transcripts) if t and str(t).strip()]
        
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


