import os
import json
import time
import requests
from datetime import datetime
from tenacity import (
    retry, wait_exponential, stop_after_attempt,
    retry_if_exception_type, before_sleep_log
)
import logging

# Configure logging for web search
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "web_search.log"),
    level=logging.INFO,
    format='%(message)s'
)

# --- Configuration ---
try:
    from config import WEB_SEARCH_API_KEY
except ImportError:
    WEB_SEARCH_API_KEY = os.environ.get("WEB_SEARCH_API_KEY")
    if not WEB_SEARCH_API_KEY:
        raise ValueError("WEB_SEARCH_API_KEY not found in config.py or environment variables.")

# --- Serper API Configuration ---
SERPER_API_URL = "https://google.serper.dev/search"


class WebSearchTool:
    def __init__(self):
        self.name = "web_search"
        self.description = "Performs a web search using the Serper API and returns structured results including titles, snippets, and URLs."
        self.parameters = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string."
                },
                "num_results": {
                    "type": "integer",
                    "description": "The maximum number of search results to return (default: 5, max: 10).",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10
                },
                "search_type": {
                    "type": "string",
                    "description": "The type of search to perform (general, news, images, videos, shopping).",
                    "enum": ["general", "news", "images", "videos", "shopping"],
                    "default": "general"
                }
            },
            "required": ["query"]
        }

    def get_tool_schema(self):
        """Returns the OpenClaw tool schema for LLM tool use."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

    def build_niche_query(self, base_query: str, niche: str = None) -> str:
        """
        Enriches a base query with the selected niche when available.
        Ensures Will's market research is always niche-specific once a niche is selected.
        """
        if niche and niche not in (None, "Not yet identified", "Not specified"):
            return f"{base_query} for {niche}"
        return base_query

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.INFO)
    )
    def _perform_serper_search(self, query, num_results, search_type):
        headers = {
            "X-API-KEY": WEB_SEARCH_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": num_results
        }

        if search_type == "news":
            payload["tbm"] = "nws"
        elif search_type == "images":
            payload["tbm"] = "isch"
        elif search_type == "videos":
            payload["tbm"] = "vid"
        elif search_type == "shopping":
            payload["tbm"] = "shop"
        # For 'general', no specific 'tbm' needed -- it's the default

        response = requests.post(SERPER_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()

    def execute(self, query: str, num_results: int = 5, search_type: str = "general", niche: str = None) -> dict:
        """
        Executes a web search via the Serper API.
        If niche is provided, the query is automatically enriched with niche context.
        """
        # Enrich query with niche context if available
        enriched_query = self.build_niche_query(query, niche)

        start_time = time.time()
        search_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        log_entry = {
            "id": search_id,
            "timestamp": datetime.now().isoformat(),
            "tool": self.name,
            "query": enriched_query,
            "original_query": query,
            "niche": niche,
            "num_results_requested": num_results,
            "search_type": search_type,
            "status": "initiated"
        }
        logging.info(json.dumps(log_entry))

        results_list = []
        status = "failed"
        error_message = None

        try:
            serper_response = self._perform_serper_search(enriched_query, num_results, search_type)

            if search_type == "news" and "news" in serper_response:
                for item in serper_response["news"]:
                    results_list.append({
                        "title": item.get("title"),
                        "snippet": item.get("snippet"),
                        "url": item.get("link")
                    })
            elif search_type == "images" and "images" in serper_response:
                for item in serper_response["images"]:
                    results_list.append({
                        "title": item.get("title"),
                        "snippet": item.get("snippet"),
                        "url": item.get("imageUrl")
                    })
            elif search_type == "videos" and "videos" in serper_response:
                for item in serper_response["videos"]:
                    results_list.append({
                        "title": item.get("title"),
                        "snippet": item.get("snippet"),
                        "url": item.get("link")
                    })
            elif search_type == "shopping" and "shopping" in serper_response:
                for item in serper_response["shopping"]:
                    results_list.append({
                        "title": item.get("title"),
                        "snippet": item.get("snippet"),
                        "url": item.get("link")
                    })
            else:
                # Default to organic results for general search
                if "organic" in serper_response:
                    for item in serper_response["organic"]:
                        results_list.append({
                            "title": item.get("title"),
                            "snippet": item.get("snippet"),
                            "url": item.get("link")
                        })

            status = "success"

        except requests.exceptions.HTTPError as e:
            status = "failed"
            error_message = f"HTTP Error: {e.response.status_code} - {e.response.text}"
            logging.error(f"Search ID: {search_id} - {error_message}")
        except requests.exceptions.ConnectionError as e:
            status = "failed"
            error_message = f"Connection Error: {e}"
            logging.error(f"Search ID: {search_id} - {error_message}")
        except requests.exceptions.Timeout as e:
            status = "failed"
            error_message = f"Timeout Error: {e}"
            logging.error(f"Search ID: {search_id} - {error_message}")
        except requests.exceptions.RequestException as e:
            status = "failed"
            error_message = f"Request Exception: {e}"
            logging.error(f"Search ID: {search_id} - {error_message}")
        except Exception as e:
            status = "failed"
            error_message = f"An unexpected error occurred: {e}"
            logging.error(f"Search ID: {search_id} - {error_message}")

        end_time = time.time()
        duration = end_time - start_time

        response_data = {
            "id": search_id,
            "timestamp": datetime.now().isoformat(),
            "query": enriched_query,
            "original_query": query,
            "niche": niche,
            "search_type": search_type,
            "num_results_returned": len(results_list),
            "results": results_list,
            "status": status,
            "duration_seconds": round(duration, 3),
            "error": error_message
        }

        logging.info(json.dumps(response_data))
        return response_data