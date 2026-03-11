import os
import time
import json
import logging
import requests
from datetime import datetime
from config import (
    HEARTBEAT_INTERVAL,
    MAX_CONSECUTIVE_FAILURES,
    DISCORD_WEBHOOK_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    LOG_FILE
)

# Ensure logs directory exists before configuring FileHandler
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/heartbeat.log"),
        logging.StreamHandler()
    ]
)


class HeartbeatTool:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.consecutive_failures = 0
        self.discord_webhook_url = DISCORD_WEBHOOK_URL
        self.telegram_bot_token = TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID
        self._log_init()

    def _log_init(self):
        self.logger.info(json.dumps({
            "event": "heartbeat_init",
            "heartbeat_interval": HEARTBEAT_INTERVAL,
            "max_consecutive_failures": MAX_CONSECUTIVE_FAILURES,
            "discord_enabled": bool(self.discord_webhook_url),
            "telegram_enabled": bool(self.telegram_bot_token and self.telegram_chat_id)
        }))

    def get_tool_schema(self) -> dict:
        return {
            "name": "heartbeat",
            "description": (
                "Monitors AgentWill's uptime and sends alerts via Discord or Telegram "
                "if the agent fails or stops responding. Call periodically to confirm Will is alive."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["alive", "error", "halted"],
                        "description": "Current agent status to report."
                    },
                    "message": {
                        "type": "string",
                        "description": "Optional status message or error detail."
                    }
                },
                "required": ["status"]
            }
        }

    def send_discord_alert(self, message: str):
        if not self.discord_webhook_url:
            return
        try:
            requests.post(self.discord_webhook_url, json={"content": message}, timeout=10)
            self.logger.info(json.dumps({"event": "discord_alert_sent", "message": message}))
        except Exception as e:
            self.logger.error(json.dumps({"event": "discord_alert_failed", "error": str(e)}))

    def send_telegram_alert(self, message: str):
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            requests.post(url, json={"chat_id": self.telegram_chat_id, "text": message}, timeout=10)
            self.logger.info(json.dumps({"event": "telegram_alert_sent", "message": message}))
        except Exception as e:
            self.logger.error(json.dumps({"event": "telegram_alert_failed", "error": str(e)}))

    def alert(self, message: str):
        self.send_discord_alert(message)
        self.send_telegram_alert(message)

    def execute(self, status: str = "alive", message: str = "") -> dict:
        timestamp = datetime.now().isoformat()

        if status == "alive":
            self.consecutive_failures = 0
            self.logger.info(json.dumps({
                "event": "heartbeat_ok",
                "timestamp": timestamp,
                "message": message
            }))
        else:
            self.consecutive_failures += 1
            alert_message = f"[AgentWill] Status: {status} | {message} | {timestamp}"
            self.logger.warning(json.dumps({
                "event": "heartbeat_alert",
                "status": status,
                "consecutive_failures": self.consecutive_failures,
                "timestamp": timestamp,
                "message": message
            }))
            self.alert(alert_message)

            if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                critical = f"[AgentWill] CRITICAL: {self.consecutive_failures} consecutive failures. Will may be down."
                self.alert(critical)
                self.logger.error(json.dumps({
                    "event": "heartbeat_critical",
                    "consecutive_failures": self.consecutive_failures
                }))

        return {
            "status": status,
            "timestamp": timestamp,
            "consecutive_failures": self.consecutive_failures,
            "message": message
        }
