import json
import requests
import time
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from config import WEB_SEARCH_API_KEY, RAPIDAPI_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG_FILE = "logs/social_research.log"


def _log(entry: dict):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


class SocialResearchTool:
    """
    Tool for performing social research across Reddit, Twitter/X,
    HackerNews, and ProductHunt. Returns structured results matching
    the web_search.py output format for seamless use in agent_will.py.
    """

    SERPER_URL     = "https://google.serper.dev/search"
    HN_URL         = "https://hn.algolia.com/api/v1/search"
    RAPIDAPI_HOST  = "twitter154.p.rapidapi.com"
    RAPIDAPI_URL   = "https://twitter154.p.rapidapi.com/search/search"

    def __init__(self):
        self.api_key = WEB_SEARCH_API_KEY       # Serper key reused for Reddit/PH via Google
        self.rapidapi_key = RAPIDAPI_KEY         # None if not set -- triggers Serper fallback
        self._log_init()

    def _log_init(self):
        _log({
            "timestamp": datetime.now().isoformat(),
            "event": "SocialResearchTool initialized",
            "rapidapi_available": self.rapidapi_key is not None
        })

    def build_niche_query(self, base_query: str, niche: str = None) -> str:
        """
        Enriches a base query with niche context when available.
        Mirrors web_search.py's build_niche_query for consistency.
        """
        if niche and niche not in (None, "Not yet identified", "Not specified"):
            return f"{base_query} for {niche}"
        return base_query

    # ------------------------------------------------------------------ #
    #  REDDIT                                                              #
    # ------------------------------------------------------------------ #
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_reddit(self, query: str, subreddit: str = None, num_results: int = 5) -> dict:
        """
        Search Reddit via Serper's Google search endpoint.
        Optionally scope to a specific subreddit.
        """
        start = time.time()
        scoped_query = f"site:reddit.com {f'subreddit:{subreddit} ' if subreddit else ''}{query}"

        try:
            response = requests.post(
                self.SERPER_URL,
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                json={"q": scoped_query, "num": num_results, "type": "search"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = [
                {
                    "title":   r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "url":     r.get("link", ""),
                    "source":  "reddit"
                }
                for r in data.get("organic", [])[:num_results]
            ]

            entry = {
                "timestamp":            datetime.now().isoformat(),
                "platform":             "reddit",
                "query":                query,
                "subreddit":            subreddit,
                "num_results_returned": len(results),
                "status":               "success",
                "duration_seconds":     round(time.time() - start, 3),
                "results":              results
            }
            _log(entry)
            return entry

        except Exception as e:
            entry = {
                "timestamp":        datetime.now().isoformat(),
                "platform":         "reddit",
                "query":            query,
                "status":           "error",
                "error":            str(e),
                "duration_seconds": round(time.time() - start, 3),
                "results":          []
            }
            _log(entry)
            return entry

    # ------------------------------------------------------------------ #
    #  TWITTER / X                                                         #
    # ------------------------------------------------------------------ #
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_twitter(self, query: str, num_results: int = 10, rapidapi_key: str = None) -> dict:
        """
        Search Twitter/X via RapidAPI Twitter scraper.
        Falls back to Serper Google search scoped to twitter.com if no key.
        """
        start = time.time()

        # Fallback: use Serper scoped to twitter.com if no RapidAPI key
        if not rapidapi_key:
            try:
                response = requests.post(
                    self.SERPER_URL,
                    headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                    json={"q": f"site:twitter.com {query}", "num": num_results, "type": "search"},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                results = [
                    {
                        "title":   r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "url":     r.get("link", ""),
                        "source":  "twitter"
                    }
                    for r in data.get("organic", [])[:num_results]
                ]

                entry = {
                    "timestamp":            datetime.now().isoformat(),
                    "platform":             "twitter",
                    "query":                query,
                    "method":               "serper_fallback",
                    "num_results_returned": len(results),
                    "status":               "success",
                    "duration_seconds":     round(time.time() - start, 3),
                    "results":              results
                }
                _log(entry)
                return entry

            except Exception as e:
                entry = {
                    "timestamp":        datetime.now().isoformat(),
                    "platform":         "twitter",
                    "query":            query,
                    "status":           "error",
                    "error":            str(e),
                    "duration_seconds": round(time.time() - start, 3),
                    "results":          []
                }
                _log(entry)
                return entry

        # Primary: RapidAPI Twitter scraper
        try:
            response = requests.get(
                self.RAPIDAPI_URL,
                headers={
                    "X-RapidAPI-Key":  rapidapi_key,
                    "X-RapidAPI-Host": self.RAPIDAPI_HOST
                },
                params={"query": query, "section": "top", "limit": num_results},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = [
                {
                    "title":    t.get("user", {}).get("username", ""),
                    "snippet":  t.get("text", ""),
                    "url":      f"https://twitter.com/i/web/status/{t.get('tweet_id', '')}",
                    "source":   "twitter",
                    "likes":    t.get("favorite_count", 0),
                    "retweets": t.get("retweet_count", 0)
                }
                for t in data.get("results", [])[:num_results]
            ]

            entry = {
                "timestamp":            datetime.now().isoformat(),
                "platform":             "twitter",
                "query":                query,
                "method":               "rapidapi",
                "num_results_returned": len(results),
                "status":               "success",
                "duration_seconds":     round(time.time() - start, 3),
                "results":              results
            }
            _log(entry)
            return entry

        except Exception as e:
            entry = {
                "timestamp":        datetime.now().isoformat(),
                "platform":         "twitter",
                "query":            query,
                "status":           "error",
                "error":            str(e),
                "duration_seconds": round(time.time() - start, 3),
                "results":          []
            }
            _log(entry)
            return entry

    # ------------------------------------------------------------------ #
    #  HACKER NEWS                                                         #
    # ------------------------------------------------------------------ #
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_hackernews(self, query: str, num_results: int = 5) -> dict:
        """
        Search HackerNews via the free Algolia HN API. No API key required.
        """
        start = time.time()

        try:
            response = requests.get(
                self.HN_URL,
                params={"query": query, "hitsPerPage": num_results, "tags": "story"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = [
                {
                    "title":    hit.get("title", ""),
                    "snippet":  hit.get("story_text", "") or hit.get("comment_text", ""),
                    "url":      hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"),
                    "source":   "hackernews",
                    "points":   hit.get("points", 0),
                    "comments": hit.get("num_comments", 0)
                }
                for hit in data.get("hits", [])[:num_results]
            ]

            entry = {
                "timestamp":            datetime.now().isoformat(),
                "platform":             "hackernews",
                "query":                query,
                "num_results_returned": len(results),
                "status":               "success",
                "duration_seconds":     round(time.time() - start, 3),
                "results":              results
            }
            _log(entry)
            return entry

        except Exception as e:
            entry = {
                "timestamp":        datetime.now().isoformat(),
                "platform":         "hackernews",
                "query":            query,
                "status":           "error",
                "error":            str(e),
                "duration_seconds": round(time.time() - start, 3),
                "results":          []
            }
            _log(entry)
            return entry

    # ------------------------------------------------------------------ #
    #  PRODUCT HUNT                                                        #
    # ------------------------------------------------------------------ #
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def search_producthunt(self, query: str, num_results: int = 5) -> dict:
        """
        Search ProductHunt via Serper Google search scoped to producthunt.com.
        """
        start = time.time()

        try:
            response = requests.post(
                self.SERPER_URL,
                headers={"X-API-KEY": self.api_key, "Content-Type": "application/json"},
                json={"q": f"site:producthunt.com {query}", "num": num_results, "type": "search"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = [
                {
                    "title":   r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "url":     r.get("link", ""),
                    "source":  "producthunt"
                }
                for r in data.get("organic", [])[:num_results]
            ]

            entry = {
                "timestamp":            datetime.now().isoformat(),
                "platform":             "producthunt",
                "query":                query,
                "num_results_returned": len(results),
                "status":               "success",
                "duration_seconds":     round(time.time() - start, 3),
                "results":              results
            }
            _log(entry)
            return entry

        except Exception as e:
            entry = {
                "timestamp":        datetime.now().isoformat(),
                "platform":         "producthunt",
                "query":            query,
                "status":           "error",
                "error":            str(e),
                "duration_seconds": round(time.time() - start, 3),
                "results":          []
            }
            _log(entry)
            return entry

    # ------------------------------------------------------------------ #
    #  COMBINED SEARCH                                                     #
    # ------------------------------------------------------------------ #
    def search_all(self, query: str, num_results: int = 5, rapidapi_key: str = None) -> dict:
        """
        Run a query across all four platforms simultaneously.
        Returns a unified dict with results keyed by platform.
        Best used in Phase 1 niche validation.
        """
        start = time.time()

        reddit      = self.search_reddit(query, num_results=num_results)
        twitter     = self.search_twitter(query, num_results=num_results, rapidapi_key=rapidapi_key)
        hackernews  = self.search_hackernews(query, num_results=num_results)
        producthunt = self.search_producthunt(query, num_results=num_results)

        combined = {
            "timestamp":        datetime.now().isoformat(),
            "query":            query,
            "duration_seconds": round(time.time() - start, 3),
            "status":           "success",
            "platforms": {
                "reddit":      reddit,
                "twitter":     twitter,
                "hackernews":  hackernews,
                "producthunt": producthunt,
            },
            "total_results": (
                reddit["num_results_returned"] +
                twitter["num_results_returned"] +
                hackernews["num_results_returned"] +
                producthunt["num_results_returned"]
            )
        }

        _log({
            "timestamp":     datetime.now().isoformat(),
            "event":         "search_all",
            "query":         query,
            "total_results": combined["total_results"],
            "duration":      combined["duration_seconds"]
        })

        return combined

    # ------------------------------------------------------------------ #
    #  OPENCLAW TOOL SCHEMA                                                #
    # ------------------------------------------------------------------ #
    def get_tool_schema(self) -> dict:
        return {
            "name": "social_research",
            "description": (
                "Search social platforms (Reddit, Twitter/X, HackerNews, ProductHunt) "
                "for real human sentiment, pain points, trends, and competitor signals. "
                "Use for niche validation in Phase 1, MVP messaging in Phase 2, "
                "early adopter outreach in Phase 3, and brand monitoring in Phase 4."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    },
                    "platform": {
                        "type": "string",
                        "enum": ["reddit", "twitter", "hackernews", "producthunt", "all"],
                        "description": "Platform to search. Use 'all' for Phase 1 niche validation."
                    },
                    "subreddit": {
                        "type": "string",
                        "description": "Optional subreddit to scope Reddit searches."
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return per platform. Default: 5."
                    }
                },
                "required": ["query", "platform"]
            }
        }

    # ------------------------------------------------------------------ #
    #  UNIFIED ENTRY POINT                                                 #
    # ------------------------------------------------------------------ #
    def execute(self, query: str, platform: str = "all", subreddit: str = None,
                num_results: int = 5, niche: str = None) -> dict:
        """
        Unified entry point matching web_search.py's .execute() interface.
        Called by agent_will.py as: self.tools["social_research"].execute(...)
        Niche context is injected into the query when available.
        """
        enriched_query = self.build_niche_query(query, niche)

        if platform == "reddit":
            return self.search_reddit(enriched_query, subreddit=subreddit, num_results=num_results)
        elif platform == "twitter":
            return self.search_twitter(enriched_query, num_results=num_results, rapidapi_key=self.rapidapi_key)
        elif platform == "hackernews":
            return self.search_hackernews(enriched_query, num_results=num_results)
        elif platform == "producthunt":
            return self.search_producthunt(enriched_query, num_results=num_results)
        else:
            return self.search_all(enriched_query, num_results=num_results, rapidapi_key=self.rapidapi_key)