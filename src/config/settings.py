import os
import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class TranslationConfig:
    enabled: bool = False
    provider: str = 'google'
    target_language: str = 'zh-CN'
    api_key: str = ''
    api_url: str = ''
    model: str = ''
    bilingual: bool = False

@dataclass
class DiarizationConfig:
    enabled: bool = False
    hf_token: str = ''

@dataclass
class AppConfig:
    language: str = 'auto'
    model_name: str = 'medium'
    device: str = 'auto'
    translation: TranslationConfig = None
    diarization: DiarizationConfig = None

    def __post_init__(self):
        if self.translation is None:
            self.translation = TranslationConfig()
        if self.diarization is None:
            self.diarization = DiarizationConfig()

class ConfigManager:
    def __init__(self, settings_path: str = 'settings.ini'):
        self.settings_path = settings_path
        self.config = AppConfig()
        self._load_config()

    def _load_config(self):
        parser = configparser.ConfigParser()
        
        if os.path.exists(self.settings_path):
            try:
                parser.read(self.settings_path, encoding='utf-8')
            except Exception as e:
                print(f"Warning: Failed to read settings.ini: {e}")

        # Load DEFAULT section
        if 'DEFAULT' in parser:
            default = parser['DEFAULT']
            self.config.language = default.get('Language', 'auto')
            self.config.model_name = default.get('Mode', 'medium')
            self.config.device = default.get('Device', 'auto')

        # Load TRANSLATION section
        if 'TRANSLATION' in parser:
            trans = parser['TRANSLATION']
            self.config.translation.enabled = trans.getboolean('Enable', False)
            self.config.translation.provider = trans.get('Provider', 'google')
            self.config.translation.target_language = trans.get('TargetLanguage', 'zh-CN')
            self.config.translation.api_key = trans.get('APIKey', '')
            self.config.translation.api_url = trans.get('APIUrl', '')
            self.config.translation.model = trans.get('Model', '')
            self.config.translation.bilingual = trans.getboolean('Bilingual', False)

        # Load DIARIZATION section
        if 'DIARIZATION' in parser:
            diar = parser['DIARIZATION']
            self.config.diarization.enabled = diar.getboolean('Enable', False)
            self.config.diarization.hf_token = diar.get('HFToken', '')

        # Save back to ensure defaults exist
        self.save_config()

    def save_config(self):
        parser = configparser.ConfigParser()
        
        parser['DEFAULT'] = {
            'Language': self.config.language,
            'Mode': self.config.model_name,
            'Device': self.config.device
        }

        parser['TRANSLATION'] = {
            'Enable': str(self.config.translation.enabled),
            'Provider': self.config.translation.provider,
            'TargetLanguage': self.config.translation.target_language,
            'APIKey': self.config.translation.api_key,
            'APIUrl': self.config.translation.api_url,
            'Model': self.config.translation.model,
            'Bilingual': str(self.config.translation.bilingual)
        }

        parser['DIARIZATION'] = {
            'Enable': str(self.config.diarization.enabled),
            'HFToken': self.config.diarization.hf_token
        }

        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                parser.write(f)
        except Exception as e:
            print(f"Warning: Failed to write settings.ini: {e}")

    def get_config(self) -> AppConfig:
        return self.config
