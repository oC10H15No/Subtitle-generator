# Video Subtitle Generator

A powerful and flexible tool for generating subtitles from video and audio files using OpenAI's Whisper model. Supports automatic speech recognition (ASR), speaker diarization, translation, and handles long files efficiently through chunked processing.

## Features

*   **High-Quality ASR**: Utilizes [OpenAI's Whisper](https://github.com/openai/whisper) model for accurate speech-to-text conversion.
*   **Speaker Diarization**: Automatically identifies and labels different speakers using [pyannote.audio](https://github.com/pyannote/pyannote-audio), perfect for interviews, conversations, and multi-speaker content.
*   **GPU Acceleration**: Supports CUDA for fast processing on NVIDIA GPUs (recommended for both ASR and diarization).
*   **Long Audio Support**: Automatically splits long audio files into chunks to manage memory usage and ensure stability.
*   **Multi-language Translation**: Integrated translation support using various providers:
    *   **Google Translate**: Free and widely available.
    *   **DeepL**: High-quality translation (requires API key).
    *   **LLM**: Support for Large Language Models via API (e.g., OpenAI, GLM) for context-aware translation.
*   **Bilingual Subtitles**: Option to generate bilingual subtitles (Translated text + Original text).
*   **Flexible Configuration**: Configure via `settings.ini` or command-line arguments.
*   **Standard Output**: Generates standard `.srt` subtitle files with optional speaker labels.

## Prerequisites

*   **Python 3.10** or higher.
*   **FFmpeg**: Must be installed and added to your system's PATH.
    *   *Ubuntu/Debian*: `sudo apt install ffmpeg`
    *   *Windows*: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add `bin` folder to Path.
*   **NVIDIA GPU** (Optional but recommended): Significantly faster processing for both Whisper and pyannote. Requires CUDA Toolkit installed.
*   **Hugging Face Token** (Required for diarization): 
    *   Create a free account at [huggingface.co](https://huggingface.co)
    *   Accept the user agreement for [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
    *   Generate an access token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/oC10H15No/Subtitle-generator.git
    cd Subtitle-generator
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment (venv or conda).

    ```bash
    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt
    ```


## Configuration

The application uses a `settings.ini` file for default configurations. You can modify this file to set your preferred defaults.

**`settings.ini` Overview:**

```ini
[DEFAULT]
language = auto          # Source language (auto, en, zh, etc.)
mode = medium            # Whisper model size (tiny, base, small, medium, large, large-v3)
device = cuda            # Processing device (cuda or cpu)

[TRANSLATION]
enable = False           # Enable translation by default
provider = llm           # Translation provider (google, deepl, llm)
targetlanguage = zh      # Target language code
apikey = your_api_key    # API Key for DeepL or LLM
apiurl = https://...     # API URL for LLM provider
model = glm-4-flash      # Model name for LLM
bilingual = True         # Output bilingual subtitles (Translated \n Original)

[DIARIZATION]
enable = True            # Enable speaker diarization by default
hftoken = hf_xxxxx       # Your Hugging Face access token
```

## Usage

Run the tool using the `run.py` script.

### Basic Usage

Generate subtitles for a video file using default settings defined in `settings.ini`:

```bash
python run.py path/to/video.mp4
```

### Command Line Arguments

You can override configuration settings using CLI arguments:

*   `filename`: Path to the video/audio file (Required).
*   `--model`: Whisper model name (tiny, base, small, medium, large, large-v3).
*   `--lang`: Source language (e.g., `en`, `zh-cn`, `auto`).
*   `--format`: Subtitle format (srt, vtt, json, raw). Default: srt.
*   `--device`: Device to use (`cuda` or `cpu`).
*   `--output`: Custom output file path.
*   `--translate`: Enable translation.
*   `--target-lang`: Target language for translation (e.g., `zh-CN`).
*   `--diarize`: Enable speaker diarization.
*   `--hf-token`: Hugging Face token for diarization (overrides config).


## Project Structure

```
.
├── run.py                  # Entry point of the application
├── settings.ini            # Configuration file
├── requirements.txt        # Python dependencies
├── src/
│   ├── cli/                # Command Line Interface logic
│   │   └── main.py         # CLI argument parsing
│   ├── config/             # Configuration management
│   │   └── settings.py     # Settings loader
│   ├── core/               # Core logic
│   │   ├── engine.py       # Whisper ASR engine
│   │   ├── chunked_asr.py  # Long audio chunking
│   │   ├── diarizer.py     # Speaker diarization
│   │   └── pipeline.py     # Main processing pipeline
│   ├── translation/        # Translation providers
│   │   ├── base.py         # Base translator interface
│   │   ├── factory.py      # Translator factory
│   │   └── providers.py    # Google, DeepL, LLM translators
│   └── utils/              # Utility functions
│       └── formatter.py    # Subtitle formatting (SRT, VTT, JSON)
└── test/                   # Test files and examples
```

## How It Works

1. **Audio Preprocessing**: Input media is converted to 16kHz mono WAV using FFmpeg for consistent processing.
2. **Speech Recognition**: Whisper transcribes audio with word-level timestamps.
3. **Speaker Diarization** (optional): Pyannote identifies speaker segments with timestamps.
4. **Speaker Assignment**: Each Whisper sentence is assigned the speaker with the longest time overlap, preserving natural sentence boundaries.
5. **Translation** (optional): Transcripts are translated in batches using the selected provider.
6. **Subtitle Generation**: Final subtitles are formatted with timestamps and speaker labels.


## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) - Speaker diarization
- [deep-translator](https://github.com/nidhaloff/deep-translator) - Translation support

