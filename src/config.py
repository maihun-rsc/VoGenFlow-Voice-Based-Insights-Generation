"""
Configuration Module for Voice-to-Insight System.
Manages environment variables, default model identifiers, audio sampling constants, and storage paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"
TEMP_AUDIO_DIR = BASE_DIR / "temp_audio"

# Ensure runtime directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# API Keys & Endpoints
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", os.getenv("LM_STUDIO_HOST", "http://localhost:1234/v1"))
DEFAULT_LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "lm-studio-bionic")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", LM_STUDIO_BASE_URL)

# STT Configuration
DEFAULT_STT_PROVIDER = os.getenv("DEFAULT_STT_PROVIDER", "groq")  # 'groq' | 'local'
DEFAULT_GROQ_STT_MODEL = os.getenv("DEFAULT_GROQ_STT_MODEL", "whisper-large-v3-turbo")
AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", "1"))
AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", "1024"))

# LLM / Insight Generation Configuration
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "groq")  # 'groq' | 'lm_studio' | 'ollama'
DEFAULT_GROQ_LLM_MODEL = os.getenv("DEFAULT_GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
DEFAULT_OLLAMA_MODEL = os.getenv("DEFAULT_OLLAMA_MODEL", DEFAULT_LM_STUDIO_MODEL)

# RAG Configuration
DEFAULT_RAG_TOP_K = int(os.getenv("DEFAULT_RAG_TOP_K", "4"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

def has_groq_key() -> bool:
    """Check if a valid Groq API key is present."""
    key = os.getenv("GROQ_API_KEY", "")
    return bool(key and key.strip() and not key.startswith("your_"))


def is_offline() -> bool:
    """Check if offline mode is explicitly forced or no key is present."""
    env_val = os.getenv("VOGENFLOW_OFFLINE_MODE", "0").lower()
    return env_val in ("1", "true", "yes", "on") or not has_groq_key()



class Config:
    """Class wrapper for configuration attributes."""
    BASE_DIR = BASE_DIR
    OUTPUT_DIR = OUTPUT_DIR
    DOCS_DIR = DOCS_DIR
    TEMP_AUDIO_DIR = TEMP_AUDIO_DIR
    GROQ_API_KEY = GROQ_API_KEY
    LM_STUDIO_BASE_URL = LM_STUDIO_BASE_URL
    DEFAULT_LM_STUDIO_MODEL = DEFAULT_LM_STUDIO_MODEL
    OLLAMA_HOST = OLLAMA_HOST
    DEFAULT_STT_PROVIDER = DEFAULT_STT_PROVIDER
    DEFAULT_GROQ_STT_MODEL = DEFAULT_GROQ_STT_MODEL
    AUDIO_SAMPLE_RATE = AUDIO_SAMPLE_RATE
    AUDIO_CHANNELS = AUDIO_CHANNELS
    AUDIO_CHUNK_SIZE = AUDIO_CHUNK_SIZE
    DEFAULT_LLM_PROVIDER = DEFAULT_LLM_PROVIDER
    DEFAULT_GROQ_LLM_MODEL = DEFAULT_GROQ_LLM_MODEL
    DEFAULT_OLLAMA_MODEL = DEFAULT_OLLAMA_MODEL
    DEFAULT_RAG_TOP_K = DEFAULT_RAG_TOP_K
    CHUNK_SIZE = CHUNK_SIZE
    CHUNK_OVERLAP = CHUNK_OVERLAP
    has_groq_key = staticmethod(has_groq_key)
    is_offline = staticmethod(is_offline)
