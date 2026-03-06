import os

AGENT_NAME = "AgentWill"
INITIAL_BUDGET = 0.0 # Starting budget for operations
TARGET_REVENUE = 50000.0
LOG_FILE = "logs/agent_will.log"

# Ethical Guidelines (simplified for example)
ETHICAL_GUIDELINES = [
    "Do not engage in deceptive marketing practices.",
    "Respect user privacy and data security.",
    "Operate within all applicable local and international laws.",
    "Prioritize long-term value creation over short-term gains."
]

# Tool Configurations
WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY", "your_web_search_api_key")
CONTENT_GENERATOR_API_KEY = os.getenv("CONTENT_GENERATOR_API_KEY", "your_content_generator_api_key")

# OpenClaw Specific Constants
OPENCLAW_MODEL = os.getenv("OPENCLAW_MODEL", "claude-3-opus-20240229") # Default to Opus if not specified
HEARTBEAT_INTERVAL = 60 # Seconds between agent heartbeats
MAX_CONSECUTIVE_FAILURES = 5 # Max failures before agent stops
