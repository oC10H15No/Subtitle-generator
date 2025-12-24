import re
from typing import List, Dict, Any

class SentenceSegmenter:
    def __init__(self, max_chars: int = 42, max_duration: float = 6.0, min_duration: float = 1.0):
        # Punctuation that marks end of sentence
        self.end_marks = re.compile(r'[.!?。！？]$')
        # Maximum characters per subtitle line
        self.max_chars = max_chars
        # Maximum duration for a subtitle line (seconds)
        self.max_duration = max_duration
        # Minimum duration for a subtitle line (seconds) - soft limit
        self.min_duration = min_duration

    def segment(self, transcription_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Re-segment based on industrial subtitle standards:
        1. Accumulate words until max chars, max duration, or strong punctuation.
        2. Force align start/end times based on first/last word.
        """
        segments = transcription_result.get('segments', [])
        if not segments:
            return []

        # 1. Flatten all words
        all_words = []
        for seg in segments:
            if 'words' in seg:
                all_words.extend(seg['words'])
            else:
                # Fallback if no word timestamps
                all_words.append({
                    'word': seg['text'],
                    'start': seg['start'],
                    'end': seg['end']
                })

        if not all_words:
            return []

        new_segments = []
        current_words = []
        current_text_len = 0
        
        for word_obj in all_words:
            word_text = word_obj['word']
            current_words.append(word_obj)
            current_text_len += len(word_text)
            
            # Calculate current duration
            current_start = current_words[0]['start']
            current_end = current_words[-1]['end']
            current_duration = current_end - current_start

            # Check 1: Strong Punctuation (Natural break)
            clean_word = word_text.strip()
            has_punct = self.end_marks.search(clean_word)
            
            # Check 2: Constraints
            is_too_long_chars = current_text_len >= self.max_chars
            is_too_long_time = current_duration >= self.max_duration
            
            # Decision Logic
            should_split = False
            
            if has_punct:
                # If we have punctuation, we prefer to split, UNLESS it's too short
                # But if it's too short, we might want to merge with next... 
                # For simplicity, we respect punctuation as a strong signal
                should_split = True
            elif is_too_long_chars or is_too_long_time:
                # Force split if constraints exceeded
                should_split = True
            
            if should_split:
                self._add_segment(new_segments, current_words)
                current_words = []
                current_text_len = 0

        # Add any remaining words
        if current_words:
            self._add_segment(new_segments, current_words)

        return new_segments

    def _add_segment(self, segments_list: List[Dict[str, Any]], words: List[Dict[str, Any]]):
        if not words:
            return
            
        start = words[0]['start']
        end = words[-1]['end']
        text = "".join([w['word'] for w in words]).strip()
        
        if not text:
            return
        
        segments_list.append({
            'start': start,
            'end': end,
            'text': text
        })
