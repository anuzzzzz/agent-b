"""Configuration for Agent B"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"

# Ensure directories exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys (for later phases)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Browser Settings
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
BROWSER_TIMEOUT = 30000  # 30 seconds

# App URLs
APP_URLS = {
    "asana": "https://app.asana.com",
    "notion": "https://www.notion.so",
    "linear": "https://linear.app",
    "wikipedia": "https://www.wikipedia.org",
    "example": "https://example.com",
}