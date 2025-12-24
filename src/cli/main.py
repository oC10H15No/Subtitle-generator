import argparse
import sys
import os

# Add project root to sys.path to ensure imports work if run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import ConfigManager
from src.core.pipeline import SubtitlePipeline

def main():
    parser = argparse.ArgumentParser(description='Video Subtitle Generator')
    parser.add_argument('filename', help='Path to the video/audio file')
    parser.add_argument('--model', default=None, help='Whisper model name (tiny, base, small, medium, large)')
    parser.add_argument('--lang', default=None, help='Source language (auto, en, zh-cn, etc.)')
    parser.add_argument('--format', default='srt', help='Subtitle format (srt, vtt, json, raw)')
    parser.add_argument('--device', default=None, help='Device to use (cpu, cuda)')
    parser.add_argument('--output', default=None, help='Output file path')

    # Translation arguments
    parser.add_argument('--translate', action='store_true', help='Enable translation')
    parser.add_argument('--target-lang', default=None, help='Target language for translation (e.g. zh-CN)')
    
    args = parser.parse_args()

    # Load config
    config_manager = ConfigManager()
    config = config_manager.get_config()

    # Override config with CLI args
    if args.model:
        config.model_name = args.model
    if args.lang:
        config.language = args.lang
    if args.device:
        config.device = args.device
    if args.translate:
        config.translation.enabled = True
    if args.target_lang:
        config.translation.target_language = args.target_lang


    # Initialize and run pipeline
    pipeline = SubtitlePipeline(config)
    pipeline.run(args.filename, args.output, args.format)

if __name__ == '__main__':
    main()
