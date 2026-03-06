import json
import time
import logging

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
    def __init__(self):
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
                "The tool will return a JSON object with 'generated_content', 'content_type', 'mrr_phase', 'quality_score', and 'quality_justification'."
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

    def _build_generation_prompt(self, content_type: str, prompt_details: str, mrr_phase: str, length: int):
        phase_instruction = self._get_phase_template(mrr_phase)
        base_prompt = (
            f"As AgentWill, an autonomous business agent aiming for $0 \u2192 $50K/month MRR, "
            f"generate the following content:\n"
            f"Content Type: {content_type.replace('_', ' ').title()}\n"
            f"MRR Phase: {mrr_phase.title()} - ({phase_instruction})\n"
            f"Specific Details/Keywords: {prompt_details}\n"
            f"Desired Length: Approximately {length} words/characters/sections (as appropriate for content type).\n"
            f"Ensure the tone, style, and messaging are perfectly aligned with the {mrr_phase} phase requirements.\n"
            f"Provide ONLY the generated content, without any conversational filler and do not provide any JSON formatting.\n"
        )

        if content_type == "marketing_slogan":
            return f"{base_prompt}Make it concise and impactful."
        elif content_type == "product_description":
            return f"{base_prompt}Focus on benefits and key features."
        elif content_type == "email_sequence":
            return f"{base_prompt}Generate a sequence of 3-5 emails, clearly separated. Structure for engagement."
        elif content_type == "seo_post":
            return f"{base_prompt}Include relevant keywords naturally. Structure with headings."
        elif content_type == "ad_copy":
            return f"{base_prompt}Short, attention-grabbing, and with a clear call to action."
        elif content_type == "landing_page_copy":
            return f"{base_prompt}Structure with headline, subheadline, key benefits, and CTA sections."
        elif content_type == "social_media_post":
            return f"{base_prompt}Concise, engaging, and suitable for platforms like Twitter or LinkedIn. Include relevant emojis/hashtags."
        return base_prompt
    
    def _build_validation_prompt(self, generated_content: str, content_type: str, mrr_phase: str, prompt_details: str):
        return (
            f"Assess the quality of the following generated \"{content_type.replace('_', ' ')}\" for AgentWill. "
            f"It's for the {mrr_phase} MRR phase, based on the details: '{prompt_details}'. "
            f"Rate it on a scale of 1-5 (5 being excellent) for relevance, tone, clarity, and effectiveness. "
            f"Provide the score and a brief justification, focused on how well it aligns with AgentWill's goals. "
            f"Return ONLY a JSON object like {{ \"score\": 4, \"justification\": \"Good alignment...\" }}\n\n"
            f"Content to assess:\n{generated_content}"
        )

    def execute(self, **kwargs):
        content_type = kwargs.get("content_type")
        prompt_details = kwargs.get("prompt")
        mrr_phase = kwargs.get("mrr_phase")
        length = kwargs.get("length", 150)

        if not all([content_type, prompt_details, mrr_phase]):
            raise ValueError("Missing required parameters: content_type, prompt, mrr_phase.")

        # Phase 1: Content Generation (handled by the agent's LLM call based on the prompt)
        generation_prompt = self._build_generation_prompt(content_type, prompt_details, mrr_phase, length)
        
        # In a real OpenClaw execution, this would be an automatic step
        # where the agent's LLM provides the 'thought' and 'action_input'
        # for the generation. Here, we simulate the 'thought' for logging.
        
        # The agent would typically invoke the LLM with this prompt
        # and get generated_content as a direct response.
        # For this tool, we assume the agent's internal LLM call for content generation has already happened.
        # The `execute` method should focus on orchestrating sub-tasks or validating previous LLM outputs.

        # For OpenClaw, the primary output of a tool like this is the generated content itself.
        # The validation step can be another LLM call orchestrated by the agent, or an internal check.
        
        # Since the instruction states "Do not make direct API calls to OpenAI or any LLM provider",
        # this execute method's role becomes preparing the prompt for the *agent* to use with its LLM,
        # and then processing the LLM's response (which is passed back into a subsequent tool call or state).
        
        # For this re-write, we assume the 'generated_content' comes from a prior LLM turn of the agent
        # that used a generation prompt. Thus, this tool's primary role shifts to validation.
        
        # To align with OpenClaw's model, the `execute` method should primarily return a prompt
        # if it needs further LLM interaction, or the final result if it's a pure deterministic tool.
        
        # Let's adjust this to return a prompt for the agent to use to GENERATE content,
        # and then a prompt for the agent to use to VALIDATE content.
        
        # The `execute` method will return a dictionary which the agent can interpret.
        # This is a key change for OpenClaw native tools.
        
        return {
            "tool_thought": "Preparing content generation and validation prompts for the agent's LLM.",
            "generation_prompt": generation_prompt,
            "validation_instructions": {
                "content_type": content_type,
                "prompt_details": prompt_details,
                "mrr_phase": mrr_phase
            },
            "next_step_hint": "Agent should use `generation_prompt` with its LLM to get content, then pass that content and `validation_instructions` to this tool's 'validate' method or a separate validation stage."
        }

    def validate_content(self, generated_content: str, content_type: str, prompt_details: str, mrr_phase: str):
        """This method is designed to be called by the Agent after it has generated content.
           It generates a prompt for the Agent's LLM to perform validation."""
        validation_prompt = self._build_validation_prompt(generated_content, content_type, mrr_phase, prompt_details)
        
        return {
            "tool_thought": "Preparing content quality validation prompt for the agent's LLM.",
            "validation_llm_prompt": validation_prompt,
            "next_step_hint": "Agent should use `validation_llm_prompt` with its LLM, then parse the JSON output to get score and justification."
        }

    def finalize_result(self, generated_content: str, validation_json_output: str, content_type: str, mrr_phase: str):
        """This method finalizes the result after validation has been performed by the Agent's LLM."""
        try:
            quality_assessment = json.loads(validation_json_output)
            quality_score = quality_assessment.get("score", 3)
            quality_justification = quality_assessment.get("justification", "Validation output could not be parsed or was incomplete.")
        except json.JSONDecodeError:
            self.logger.warning(f"Failed to decode validation JSON: {validation_json_output}")
            quality_score = 3
            quality_justification = "Automated validation output was malformed. Default score assigned."

        result = {
            "generated_content": generated_content,
            "content_type": content_type,
            "mrr_phase": mrr_phase,
            # Token usage cannot be directly calculated by the tool now, as LLM calls are external to it.
            # token_usage: This should ideally come from the agent's LLM call metadata.
            "quality_score": quality_score,
            "quality_justification": quality_justification,
            "timestamp": time.time() # This timestamp now represents when the final result was assembled.
        }

        self.logger.info(json.dumps({
            "timestamp": result["timestamp"],
            "event": "content_generation_finalized",
            "content_type": content_type,
            "mrr_phase": mrr_phase,
            "quality_score": quality_score,
            "summary_content_start": generated_content[:100] + "..." if len(generated_content) > 100 else generated_content,
        }))

        return result

# Example Usage (for testing the structure, not direct execution in OpenClaw way)
if __name__ == '__main__':
    tool = ContentGeneratorTool()

    # Simulate the first call to execute, getting generation and validation prompts
    initial_output = tool.execute(
        content_type="marketing_slogan",
        prompt="AI-powered business automation platform",
        mrr_phase="discovery",
        length=20
    )
    print("\n--- Initial Tool Execution (provides prompts) ---")
    print(json.dumps(initial_output, indent=2))

    # Simulate agent using generation_prompt to get content
    # In a real scenario, this would be an LLM call by the agent
    simulated_generated_content = "AgentWill: Automate Growth, Multiply MRR."
    print(f"\nSimulated Agent Generated Content: {simulated_generated_content}")

    # Simulate agent then calling validate_content with the generated content
    validation_prompts = tool.validate_content(
        generated_content=simulated_generated_content,
        content_type=initial_output["validation_instructions"]["content_type"],
        prompt_details=initial_output["validation_instructions"]["prompt_details"],
        mrr_phase=initial_output["validation_instructions"]["mrr_phase"]
    )
    print("\n--- Validation Prompt from Tool ---")
    print(json.dumps(validation_prompts, indent=2))

    # Simulate agent using validation_llm_prompt to get validation output
    # In a real scenario, this would be an LLM call by the agent
    simulated_validation_output = '{"score": 5, "justification": "Highly relevant, concise, and impactful for discovery phase. Clearly communicates value."}'
    print(f"\nSimulated Agent Validation LLM Output: {simulated_validation_output}")

    # Simulate agent then calling finalize_result with all information
    final_result = tool.finalize_result(
        generated_content=simulated_generated_content,
        validation_json_output=simulated_validation_output,
        content_type=initial_output["validation_instructions"]["content_type"],
        mrr_phase=initial_output["validation_instructions"]["mrr_phase"]
    )
    print("\n--- Final Result from Tool ---")
    print(json.dumps(final_result, indent=2))
