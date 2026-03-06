import openai
import json
import time
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

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
    def __init__(self, api_key: str = None):
        if not api_key:
            raise ValueError("OpenAI API key must be provided for ContentGeneratorTool.")
        self.api_key = api_key
        openai.api_key = api_key
        self.logger = logging.getLogger(__name__)

    def tool_schema(self):
        return {
            "name": "content_generator",
            "description": (
                "Generates various types of textual content (e.g., marketing slogans, product descriptions, "
                "email sequences, SEO posts, ad copy, landing page copy, social media posts) "
                "tailored to AgentWill's current MRR phase (discovery, validation, growth, scaling, expansion). "
                "Returns structured content along with metadata like token usage and a quality score." 
                "This tool helps AgentWill produce specific content pieces needed for business operations, marketing, and sales."
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
                        "description": "The type of content to generate. Choose from specific marketing or sales materials.",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Specific details, keywords, or requirements for the content generation. Be as descriptive as possible.",
                    },
                    "mrr_phase": {
                        "type": "string",
                        "enum": ["discovery", "validation", "growth", "scaling", "expansion"],
                        "description": "The current MRR phase of AgentWill, influencing content style and tone. This adjusts the output for target audience and business goals.",
                    },
                    "length": {
                        "type": "integer",
                        "description": "Desired length of the content in words or sections, if applicable. Defaults to 150.",
                        "default": 150,
                    },
                },
                "required": ["content_type", "prompt", "mrr_phase"],
            },
        }

    def _get_phase_template(self, mrr_phase: str):
        templates = {
            "discovery": "Initial exploration, emphasize problem-solution, clarity, and value proposition.",
            "validation": "Focus on unique selling points, early adopter benefits, and trust-building.",
            "growth": "Highlight scalability, proven results, and competitive advantages.",
            "scaling": "Emphasize market leadership, efficiency, and future vision.",
            "expansion": "Target new markets/features, innovation, and long-term partnership.",
        }
        return templates.get(mrr_phase, templates["growth"]) # Default to growth if phase is unknown

    def _build_prompt(self, content_type: str, prompt_details: str, mrr_phase: str, length: int):
        phase_instruction = self._get_phase_template(mrr_phase)
        base_prompt = (
            f"As AgentWill, an autonomous business agent aiming for $0 → $50K/month MRR, "
            f"generate the following content:\n"
            f"Content Type: {content_type.replace('_', ' ').title()}\n"
            f"MRR Phase: {mrr_phase.title()} - ({phase_instruction})\n"
            f"Specific Details/Keywords: {prompt_details}\n"
            f"Desired Length: Approximately {length} words/characters/sections (as appropriate for content type).\n"
            f"Ensure the tone, style, and messaging are perfectly aligned with the {mrr_phase} phase requirements.\n"
            f"Provide only the generated content, without any conversational filler."
        )

        if content_type == "marketing_slogan":
            return f"{base_prompt}\nMake it concise and impactful."
        elif content_type == "product_description":
            return f"{base_prompt}\nFocus on benefits and key features."
        elif content_type == "email_sequence":
            return f"{base_prompt}\nGenerate a sequence of 3-5 emails, clearly separated. Structure for engagement."
        elif content_type == "seo_post":
            return f"{base_prompt}\nInclude relevant keywords naturally. Structure with headings."
        elif content_type == "ad_copy":
            return f"{base_prompt}\nShort, attention-grabbing, and with a clear call to action."
        elif content_type == "landing_page_copy":
            return f"{base_prompt}\nStructure with headline, subheadline, key benefits, and CTA sections."
        elif content_type == "social_media_post":
            return f"{base_prompt}\nConcise, engaging, and suitable for platforms like Twitter or LinkedIn. Include relevant emojis/hashtags."
        return base_prompt

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((openai.APIError, openai.Timeout))
    )
    def _call_openai_api(self, messages):
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview", # Or gpt-3.5-turbo, depending on cost/quality needs
            messages=messages,
            temperature=0.7,
        )
        return response

    def _validate_quality(self, generated_content: str, content_type: str, mrr_phase: str, prompt_details: str):
        validation_prompt = (
            f"Assess the quality of the following generated \"{content_type.replace('_', ' ')}\" for AgentWill. "
            f"It's for the {mrr_phase} MRR phase, based on the details: '{prompt_details}'. "
            f"Rate it on a scale of 1-5 (5 being excellent) for relevance, tone, clarity, and effectiveness. "
            f"Provide the score and a brief justification, focused on how well it aligns with AgentWill's goals. "
            f"Return ONLY a JSON object like {{ \"score\": 4, \"justification\": \"Good alignment...\" }}\n\n"
            f"Content to assess:\n{generated_content}"
        )
        try:
            validation_response = self._call_openai_api(
                messages=[{"role": "system", "content": "You are an AI assistant specialized in content quality assessment."}, 
                          {"role": "user", "content": validation_prompt}]
            )
            quality_output = validation_response.choices[0].message.content.strip()
            self.logger.info(f"Quality validation response: {quality_output}")
            return json.loads(quality_output)
        except Exception as e:
            self.logger.error(f"Error validating content quality: {e}")
            return {"score": 3, "justification": "Automated validation failed. Default score assigned."}

    def generate_content(self, content_type: str, prompt: str, mrr_phase: str, length: int = 150):
        full_prompt = self._build_prompt(content_type, prompt, mrr_phase, length)
        messages = [
            {"role": "system", "content": "You are AgentWill's specialized content generation AI."}, 
            {"role": "user", "content": full_prompt},
        ]
        request_timestamp = time.time()
        log_entry = {
            "timestamp": request_timestamp,
            "event": "content_generation_request",
            "content_type": content_type,
            "mrr_phase": mrr_phase,
            "prompt_details": prompt,
            "requested_length": length,
            "full_prompt_sent": full_prompt,
        }
        self.logger.info(json.dumps(log_entry))

        try:
            response = self._call_openai_api(messages)
            generated_text = response.choices[0].message.content.strip()
            token_usage = response.usage.to_dict()
            response_timestamp = time.time()

            quality_assessment = self._validate_quality(generated_text, content_type, mrr_phase, prompt)

            result = {
                "generated_content": generated_text,
                "content_type": content_type,
                "mrr_phase": mrr_phase,
                "token_usage": token_usage,
                "timestamp": response_timestamp,
                "quality_score": quality_assessment.get("score"),
                "quality_justification": quality_assessment.get("justification"),
            }

            log_entry_response = {
                "timestamp": response_timestamp,
                "event": "content_generation_success",
                "content_type": content_type,
                "mrr_phase": mrr_phase,
                "token_usage": token_usage,
                "quality_score": quality_assessment.get("score"),
                "summary_content_start": generated_text[:100] + "..." if len(generated_text) > 100 else generated_text,
            }
            self.logger.info(json.dumps(log_entry_response))

            return result

        except openai.APIError as e:
            error_msg = f"OpenAI API error during content generation: {e}"
            self.logger.error(json.dumps({"timestamp": time.time(), "event": "content_generation_error", "error": str(e), "content_type": content_type, "mrr_phase": mrr_phase}))
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            self.logger.error(json.dumps({"timestamp": time.time(), "event": "content_generation_unexpected_error", "error": str(e), "content_type": content_type, "mrr_phase": mrr_phase}))
            raise RuntimeError(error_msg) from e

if __name__ == '__main__':
    # Example Usage (replace with your actual API key and uncomment)
    # from dotenv import load_dotenv
    # import os
    # load_dotenv()
    # api_key = os.getenv("OPENAI_API_KEY")
    # if not api_key:
    #     print("Please set OPENAI_API_KEY environment variable.")
    # else:
    #     tool = ContentGeneratorTool(api_key=api_key)
    #     try:
    #         # Test marketing slogan
    #         slogan = tool.generate_content(
    #             content_type="marketing_slogan",
    #             prompt="AI-powered business automation platform",
    #             mrr_phase="discovery",
    #             length=20
    #         )
    #         print("\nGenerated Slogan:", slogan)
    #
    #         # Test product description for growth phase
    #         product_desc = tool.generate_content(
    #             content_type="product_description",
    #             prompt="A tool that automates lead nurturing via personalized emails.",
    #             mrr_phase="growth",
    #             length=100
    #         )
    #         print("\nGenerated Product Description:", product_desc)
    #
    #         # Test an email sequence for validation phase
    #         email_seq = tool.generate_content(
    #             content_type="email_sequence",
    #             prompt="Follow-up emails for users who signed up for a free trial but haven't used it.",
    #             mrr_phase="validation",
    #             length=300
    #         )
    #         print("\nGenerated Email Sequence:", email_seq)
    #
    #         # Test social media post for scaling phase
    #         social_post = tool.generate_content(
    #             content_type="social_media_post",
    #             prompt="Promote a new case study about 10x ROI for clients.",
    #             mrr_phase="scaling",
    #             length=60
    #         )
    #         print("\nGenerated Social Media Post:", social_post)
    #
    #     except RuntimeError as e:
    #         print(f"Tool execution failed: {e}")
