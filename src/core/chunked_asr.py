import os
from typing import List, Dict, Any
from pydub import AudioSegment
import tempfile

class ChunkedASR:
    """
    Handles splitting of long audio files for ASR processing.
    Inspired by VideoCaptioner's ChunkedASR.
    """
    def __init__(self, engine, chunk_length_ms=600000, overlap_ms=10000):
        """
        :param engine: The WhisperEngine instance
        :param chunk_length_ms: Length of each chunk in ms (default 10 mins)
        :param overlap_ms: Overlap between chunks in ms (default 10s)
        """
        self.engine = engine
        self.chunk_length_ms = chunk_length_ms
        self.overlap_ms = overlap_ms

    def transcribe(self, audio_path: str, language: str = 'auto') -> Dict[str, Any]:
        """
        Transcribe audio file, splitting if necessary.
        """
        try:
            audio = AudioSegment.from_file(audio_path)
        except Exception as e:
            print(f"Error loading audio with pydub: {e}")
            print("Falling back to direct transcription.")
            return self.engine.transcribe(audio_path, language)

        duration_ms = len(audio)
        
        # If audio is short enough, just transcribe directly
        if duration_ms <= self.chunk_length_ms:
            return self.engine.transcribe(audio_path, language)

        print(f"Audio duration: {duration_ms/1000:.2f}s. Splitting into chunks...")
        
        chunks = []
        start = 0
        while start < duration_ms:
            end = min(start + self.chunk_length_ms, duration_ms)
            chunks.append((start, end))
            if end == duration_ms:
                break
            start += self.chunk_length_ms - self.overlap_ms

        all_segments = []
        
        # Process chunks
        # Note: For local Whisper, we process sequentially to avoid VRAM OOM.
        # If we had multiple GPUs or API, we could parallelize.
        for i, (start, end) in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}: {start/1000:.1f}s - {end/1000:.1f}s")
            
            chunk_audio = audio[start:end]
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                chunk_audio.export(tmp.name, format="wav")
                tmp_path = tmp.name

            try:
                result = self.engine.transcribe(tmp_path, language)
                
                # Adjust timestamps
                offset_sec = start / 1000.0
                for segment in result.get('segments', []):
                    # Skip segments in the overlap area if they are not the last chunk
                    # This is a simplified merge strategy. 
                    # A robust one would check for duplicate text.
                    seg_start = segment['start'] + offset_sec
                    seg_end = segment['end'] + offset_sec
                    
                    # Simple overlap handling:
                    # If it's not the first chunk, ignore segments that start before the overlap region ends
                    # (This is tricky without complex alignment, so we just append all and sort/filter later if needed)
                    # For now, we just trust Whisper's timestamps and shift them.
                    
                    segment['start'] = seg_start
                    segment['end'] = seg_end
                    
                    # Adjust word timestamps if available
                    if 'words' in segment:
                        for word in segment['words']:
                            word['start'] += offset_sec
                            word['end'] += offset_sec
                            
                    all_segments.append(segment)
                    
            finally:
                os.unlink(tmp_path)

        # Sort segments by start time
        all_segments.sort(key=lambda x: x['start'])
        
        return {
            "text": " ".join([s['text'] for s in all_segments]),
            "segments": all_segments,
            "language": language # Simplified
        }
