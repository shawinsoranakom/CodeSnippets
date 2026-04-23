def _detect_provider_from_model(model_name: str | None) -> str | None:
        """Detect provider from model name for gen_ai.provider.name attribute.

        Pattern matching enables provider detection without database lookups or complex
        configuration, making traces self-contained and parseable by observability tools.
        """
        if not model_name:
            return None

        model_lower = model_name.lower()

        # Pattern-based detection works across different LangChain integrations
        if "gpt" in model_lower or "o1" in model_lower or model_lower.startswith("text-"):
            return "openai"
        if "claude" in model_lower:
            return "anthropic"
        if "gemini" in model_lower or "palm" in model_lower:
            return "google"
        if "llama" in model_lower:
            return "meta"
        if "mistral" in model_lower or "mixtral" in model_lower:
            return "mistral"
        if "command" in model_lower or "coral" in model_lower:
            return "cohere"
        if "titan" in model_lower or "nova" in model_lower:
            return "amazon"
        if "azure" in model_lower:
            return "azure"

        return None