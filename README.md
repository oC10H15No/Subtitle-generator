# Video Subtitle Generator

A powerful and flexible tool for generating subtitles from video and audio files using OpenAI's Whisper model. It supports automatic speech recognition (ASR), translation, and handles long files efficiently through chunked processing.

## Features

*   **High-Quality ASR**: Utilizes [OpenAI's Whisper](https://github.com/openai/whisper) model for accurate speech-to-text conversion.
*   **GPU Acceleration**: Supports CUDA for fast processing on NVIDIA GPUs.
*   **Long Audio Support**: Automatically splits long audio files into chunks to manage memory usage and ensure stability.
*   **Multi-language Translation**: Integrated translation support using various providers:
    *   **Google Translate**: Free and widely available.
    *   **DeepL**: High-quality translation (requires API key).
    *   **LLM**: Support for Large Language Models via API (e.g., OpenAI, GLM) for context-aware translation.
*   **Bilingual Subtitles**: Option to generate bilingual subtitles (Translated text + Original text).
*   **Flexible Configuration**: Configure via `settings.ini` or command-line arguments.
*   **Standard Output**: Generates standard `.srt` subtitle files.

## Prerequisites

*   **Python 3.10** or higher.
*   **FFmpeg**: Must be installed and added to your system's PATH.
    *   *Ubuntu/Debian*: `sudo apt install ffmpeg`
    *   *Windows*: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add `bin` folder to Path.
*   **NVIDIA GPU** (Optional): Recommended for faster processing. Requires CUDA Toolkit installed.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd video-subtitle-generator
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment (venv or uv).

    ```bash
    # Using pip
    pip install -r requirements.txt
    ```

    *Note: This project currently requires `numpy<2` to ensure compatibility with the specific PyTorch version used.*

## Configuration

The application uses a `settings.ini` file for default configurations. You can modify this file to set your preferred defaults.

**`settings.ini` Overview:**

```ini
[DEFAULT]
language = auto          # Source language (auto, en, zh, etc.)
mode = medium            # Whisper model size (tiny, base, small, medium, large)
device = cuda            # Processing device (cuda or cpu)

[TRANSLATION]
enable = False           # Enable translation by default
provider = llm           # Translation provider (google, deepl, llm)
targetlanguage = en      # Target language code
apikey = your_api_key    # API Key for DeepL or LLM
apiurl = https://...     # API URL for LLM provider
model = glm-4-flash      # Model name for LLM
bilingual = True         # Output bilingual subtitles (Translated \n Original)
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
*   `--model`: Whisper model name (tiny, base, small, medium, large).
*   `--lang`: Source language (e.g., `en`, `zh-cn`).
*   `--device`: Device to use (`cuda` or `cpu`).
*   `--output`: Custom output file path.
*   `--translate`: Enable translation.
*   `--target-lang`: Target language for translation (e.g., `zh-CN`).

### Examples

**1. Use a specific model size:**
```bash
python run.py video.mp4 --model large-v3
```

**2. Generate subtitles and translate to Chinese:**
```bash
python run.py video.mp4 --translate --target-lang zh-CN
```

**3. Force CPU usage:**
```bash
python run.py video.mp4 --device cpu
```

## Project Structure

```
.
├── run.py                  # Entry point of the application
├── settings.ini            # Configuration file
├── requirements.txt        # Python dependencies
├── src/
│   ├── cli/                # Command Line Interface logic
│   ├── config/             # Configuration management
│   ├── core/               # Core logic (ASR Engine, Pipeline, Chunking)
│   ├── translation/        # Translation providers (Google, DeepL, LLM)
│   └── utils/              # Utility functions (Formatting, etc.)
└── test/                   # Test files
```

## Troubleshooting

*   **`RuntimeError: Numpy is not available`**: This usually happens if `numpy` version 2.x is installed with an incompatible PyTorch version. Ensure you have `numpy<2` installed:
    ```bash
    pip install "numpy<2"
    ```
*   **`CUDA not available`**: Ensure you have installed the correct version of PyTorch for your CUDA version. Check [pytorch.org](https://pytorch.org/) for installation commands.

## License

[MIT License](LICENSE)
