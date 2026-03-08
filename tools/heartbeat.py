import os
import time
import requests
import logging
from datetime import datetime

# Configure logging
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
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.agent_will_status_endpoint = os.getenv("AGENT_WILL_STATUS_ENDPOINT", "http://localhost:8000/status") # Default to a common local endpoint
        self.last_successful_check = None
        logging.info("HeartbeatTool initialized.")

    def _send_discord_alert(self, message: str):
        if not self.discord_webhook_url:
            logging.warning("Discord webhook URL not configured. Cannot send alert.")
            return
        try:
            payload = {"content": message}
            response = requests.post(self.discord_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Discord alert sent successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send Discord alert: {e}")

    def _send_telegram_alert(self, message: str):
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logging.warning("Telegram bot token or chat ID not configured. Cannot send alert.")
            return
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {"chat_id": self.telegram_chat_id, "text": message}
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logging.info("Telegram alert sent successfully.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send Telegram alert: {e}")

    def _check_agent_will_status(self) -> bool:
        try:
            response = requests.get(self.agent_will_status_endpoint, timeout=5)
            response.raise_for_status()
            status_data = response.json()
            if status_data.get("status") == "running":
                return True
            else:
                logging.warning(f"AgentWill status endpoint returned non-running status: {status_data}")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to reach AgentWill status endpoint {self.agent_will_status_endpoint}: {e}")
            return False

    def run_heartbeat_check(self):
        logging.info("Running heartbeat check for AgentWill...")
        is_running = self._check_agent_will_status()

        if is_running:
            self.last_successful_check = datetime.now()
            logging.info("AgentWill is running normally.")
        else:
            alert_message = f"ALERT: AgentWill is not responding or not running! Last successful check: {self.last_successful_check.isoformat() if self.last_successful_check else 'Never'}"
            logging.critical(alert_message)
            self._send_discord_alert(alert_message)
            self._send_telegram_alert(alert_message)

    def tool_schema(self):
        return {
            "name": "heartbeat_monitor",
            "description": (
                "Monitors the operational status of AgentWill. "
                "It checks a predefined status endpoint and sends alerts via Discord/Telegram "
                "if AgentWill is detected as not running. Designed to be run as a cron job."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

    def execute(self):
        """
        Executes a single heartbeat check. This method is designed to be called by the agent
        or an external scheduler (like a cron job).
        """
        self.run_heartbeat_check()
        return {"status": "Heartbeat check completed. Check logs for details."}

if __name__ == "__main__":
    # Example of how this might be run as a standalone script or by a cron job
    # For actual deployment, ensure environment variables are set:
    # DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, AGENT_WILL_STATUS_ENDPOINT

    heartbeat = HeartbeatTool()
    heartbeat.run_heartbeat_check()

    # To simulate a cron job, you would typically schedule `python tools/heartbeat.py`
    # to run every 30 minutes. The tool itself doesn't loop indefinitely.
