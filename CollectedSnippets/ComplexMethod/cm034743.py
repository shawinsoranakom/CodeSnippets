def get_driver_for_model(model: str) -> str:
        """Determine the appropriate driver based on the model name."""
        if "openrouter:" in model:
            return "openrouter"
        elif model in PuterJS.openai_models or model.startswith("gpt-"):
            return "openai-completion"
        elif model in PuterJS.mistral_models:
            return "mistral"
        elif "grok" in model:
            return "xai"
        elif "claude" in model:
            return "claude"
        elif "deepseek" in model:
            return "deepseek"
        elif "gemini" in model:
            return "gemini"
        else:
            raise ModelNotFoundError(f"Model {model} not found in known drivers")