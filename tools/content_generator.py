class ContentGeneratorTool:
    def __init__(self, api_key=None):
        self.api_key = api_key # In a real scenario, this would configure an actual LLM/content gen API

    def generate_text(self, prompt, length=50):
        # Simulate content generation
        print(f"[Content Generator Tool] Generating content for prompt: {prompt}")
        if "marketing slogan" in prompt:
            return "AgentWill: Autonomously Building Your Future."
        elif "product description" in prompt:
            return "An AI-powered solution for automated business growth and scaling."
        return f"Generated content based on '{prompt}' limited to {length} characters.\n" * int(length/50)

