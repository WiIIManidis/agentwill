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
WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY")
if not WEB_SEARCH_API_KEY:
    raise EnvironmentError("WEB_SEARCH_API_KEY environment variable not set.")

CONTENT_GENERATOR_API_KEY = os.getenv("CONTENT_GENERATOR_API_KEY")
if not CONTENT_GENERATOR_API_KEY:
    raise EnvironmentError("CONTENT_GENERATOR_API_KEY environment variable not set.")

# OpenClaw Specific Constants
OPENCLAW_MODEL = os.getenv("OPENCLAW_MODEL", "claude-3-sonnet-20240229") # Default to Sonnet if not specified
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", 1800)) # Seconds between agent heartbeats
MAX_CONSECUTIVE_FAILURES = int(os.getenv("MAX_CONSECUTIVE_FAILURES", 3)) # Max failures before agent stops
