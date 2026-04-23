def get_models(self, *, tool_model_enabled: bool | None = None) -> list[str]:
        """Get available Groq models using the dynamic discovery system.

        This method uses the groq_model_discovery module which:
        - Fetches models directly from Groq API
        - Automatically tests tool calling support
        - Caches results for 24 hours
        - Falls back to hardcoded list if API fails

        Args:
            tool_model_enabled: If True, only return models that support tool calling

        Returns:
            List of available model IDs
        """
        try:
            # Get models with metadata from dynamic discovery system
            api_key = self.api_key if hasattr(self, "api_key") and self.api_key else None
            models_metadata = get_groq_models(api_key=api_key)

            # Filter out non-LLM models (audio, TTS, guards)
            model_ids = [
                model_id for model_id, metadata in models_metadata.items() if not metadata.get("not_supported", False)
            ]

            # Filter by tool calling support if requested
            if tool_model_enabled:
                model_ids = [model_id for model_id in model_ids if models_metadata[model_id].get("tool_calling", False)]
                logger.info(f"Loaded {len(model_ids)} Groq models with tool calling support")
            else:
                logger.info(f"Loaded {len(model_ids)} Groq models")
        except (ValueError, KeyError, TypeError, ImportError):
            logger.exception("Error getting model names")
            # Fallback to hardcoded list from groq_constants.py
            return GROQ_MODELS
        else:
            return model_ids