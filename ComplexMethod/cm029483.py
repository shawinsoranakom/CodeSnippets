def _get_variant_models(
        self,
        generation_type: Literal["create", "update"],
        input_mode: InputMode,
        num_variants: int,
        openai_api_key: str | None,
        anthropic_api_key: str | None,
        gemini_api_key: str | None,
    ) -> List[Llm]:
        """Simple model cycling that scales with num_variants"""

        # Video mode requires Gemini - 2 variants for comparison
        if input_mode == "video":
            if not gemini_api_key:
                raise Exception(
                    "Video mode requires a Gemini API key. "
                    "Please add GEMINI_API_KEY to backend/.env or in the settings dialog"
                )
            return list(VIDEO_VARIANT_MODELS)

        # Define models based on available API keys
        if gemini_api_key and anthropic_api_key and openai_api_key:
            if input_mode == "text" and generation_type == "create":
                models = list(ALL_KEYS_MODELS_TEXT_CREATE)
            elif generation_type == "update":
                models = list(ALL_KEYS_MODELS_UPDATE)
            else:
                models = list(ALL_KEYS_MODELS_DEFAULT)
        elif gemini_api_key and anthropic_api_key:
            models = list(GEMINI_ANTHROPIC_MODELS)
        elif gemini_api_key and openai_api_key:
            models = list(GEMINI_OPENAI_MODELS)
        elif openai_api_key and anthropic_api_key:
            models = list(OPENAI_ANTHROPIC_MODELS)
        elif gemini_api_key:
            models = list(GEMINI_ONLY_MODELS)
        elif anthropic_api_key:
            models = list(ANTHROPIC_ONLY_MODELS)
        elif openai_api_key:
            models = list(OPENAI_ONLY_MODELS)
        else:
            raise Exception("No OpenAI or Anthropic key")

        # Cycle through models: [A, B] with num=5 becomes [A, B, A, B, A]
        selected_models: List[Llm] = []
        for i in range(num_variants):
            selected_models.append(models[i % len(models)])

        return selected_models