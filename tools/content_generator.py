import os
import json
import time
import logging
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, OPENCLAW_MODEL

# Ensure logs directory exists before configuring FileHandler
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/content_generator.log"),
        logging.StreamHandler()
    ]
)


class ContentGeneratorTool:
    # Maps budget_manager.py phase names to content tone instructions
    PHASE_TEMPLATES = {
        "Seed":      "Initial exploration, emphasize problem-solution, clarity, and value proposition.",
        "Pre-Seed":  "Focus on unique selling points, early adopter benefits, and trust-building.",
        "Series A":  "Highlight scalability, proven results, and competitive advantages.",
        "Series B":  "Emphasize market leadership, efficiency, and future vision.",
        "Series C":  "Target new markets and features, innovation, and long-term partnership.",
        "IPO":       "Reinforce brand authority, investor confidence, and market dominance.",
        "Exit Prep": "Maximize perceived value, demonstrate traction, and highlight strategic fit.",
    }

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.logger = logging.getLogger(__name__)

    def get_tool_schema(self) -> dict:
        return {
            "name": "content_generator",
            "description": (
                "Generates marketing and sales content (slogans, product descriptions, email sequences, "
                "SEO posts, ad copy, landing page copy, social media posts) tailored to AgentWill's "
                "current MRR phase. Returns generated content with a quality score."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content_type": {
                        "type": "string",
                        "enum": [
                            "marketing_slogan",
                            "product_description",
                            "email_sequence",
                            "seo_post",
                            "ad_copy",
                            "landing_page_copy",
                            "social_media_post"
                        ],
                        "description": "The type of content to generate."
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Specific details, keywords, or requirements for content generation."
                    },
                    "mrr_phase": {
                        "type": "string",
                        "description": "Current MRR phase (Seed, Pre-Seed, Series A, Series B, Series C, IPO, Exit Prep)."
                    },
                    "length": {
                        "type": "integer",
                        "description": "Desired length in words. Defaults to 150.",
                        "default": 150
                    }
                },
                "required": ["content_type", "prompt", "mrr_phase"]
            }
        }

    def _get_phase_template(self, mrr_phase: str) -> str:
        return self.PHASE_TEMPLATES.get(mrr_phase, self.PHASE_TEMPLATES["Series A"])

    def _build_generation_prompt(self, content_type: str, prompt_details: str, mrr_phase: str, length: int) -> str:
        phase_instruction = self._get_phase_template(mrr_phase)
        base_prompt = (
            f"As AgentWill, an autonomous business agent aiming for $0 to $50K/month MRR, "
            f"generate the following content:\n"
            f"Content Type: {content_type.replace('_', ' ').title()}\n"
            f"MRR Phase: {mrr_phase} - ({phase_instruction})\n"
            f"Specific Details/Keywords: {prompt_details}\n"
            f"Desired Length: Approximately {length} words.\n"
            f"Ensure tone and messaging align with the {mrr_phase} phase.\n"
            f"Provide ONLY the generated content, no preamble, no JSON formatting.\n"
        )

        type_instructions = {
            "marketing_slogan":   "Make it concise and impactful.",
            "product_description": "Focus on benefits and key features.",
            "email_sequence":     "Generate 3-5 emails, clearly separated, structured for engagement.",
            "seo_post":           "Include relevant keywords naturally. Structure with headings.",
            "ad_copy":            "Short, attention-grabbing, with a clear call to action.",
            "landing_page_copy":  "Structure with headline, subheadline, key benefits, and CTA sections.",
            "social_media_post":  "Concise, engaging, suitable for Twitter or LinkedIn. Include relevant hashtags."
        }

        return base_prompt + type_instructions.get(content_type, "")

    def execute(self, content_type: str, prompt: str, mrr_phase: str, length: int = 150) -> dict:
        """
        Generates content via a real Anthropic API call.
        Called by agent_will.py as: self.tools["content_generator"].execute(...)
        """
        if not all([content_type, prompt, mrr_phase]):
            raise ValueError("Missing required parameters: content_type, prompt, mrr_phase.")

        generation_prompt = self._build_generation_prompt(content_type, prompt, mrr_phase, length)

        try:
            response = self.client.messages.create(
                model=OPENCLAW_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": generation_prompt}]
            )
            generated_content = response.content[0].text.strip()
        except Exception as e:
            self.logger.error(f"Content generation API call failed: {e}")
            generated_content = f"[Content generation failed: {e}]"

        result = {
            "generated_content":  generated_content,
            "generation_prompt":  generation_prompt,
            "content_type":       content_type,
            "mrr_phase":          mrr_phase,
            "timestamp":          time.time()
        }

        self.logger.info(json.dumps({
            "event":        "content_generated",
            "content_type": content_type,
            "mrr_phase":    mrr_phase,
            "preview":      generated_content[:100] + "..." if len(generated_content) > 100 else generated_content
        }))

        return result