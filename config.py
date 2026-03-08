from dotenv import load_dotenv
load_dotenv()

import os

AGENT_NAME = "Will"
VERSION = "0.1.0"
INITIAL_BUDGET = 0.0
TARGET_REVENUE = 50000.0
LOG_FILE = "logs/agent_will.log"
STATE_FILE = "state.json"

ETHICAL_GUIDELINES = [
    "Do not engage in deceptive marketing practices.",
    "Respect user privacy and data security.",
    "Operate within all applicable local and international laws.",
    "Prioritize long-term value creation over short-term gains."
]

WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY")
if not WEB_SEARCH_API_KEY:
    raise EnvironmentError("WEB_SEARCH_API_KEY environment variable not set.")

CONTENT_GENERATOR_API_KEY = os.getenv("CONTENT_GENERATOR_API_KEY")
if not CONTENT_GENERATOR_API_KEY:
    raise EnvironmentError("CONTENT_GENERATOR_API_KEY environment variable not set.")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")  # Optional: unlocks full Twitter/X data via RapidAPI

OPENCLAW_MODEL = os.getenv("OPENCLAW_MODEL", "claude-sonnet-4-6")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 1800))
MAX_CONSECUTIVE_FAILURES = int(os.getenv("MAX_CONSECUTIVE_FAILURES", 3))