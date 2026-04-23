def get_models(self, *, tool_model_enabled: bool | None = None) -> list[str]:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)
            models = client.models.list(limit=20).data
            model_ids = ANTHROPIC_MODELS + [model.id for model in models]
        except (ImportError, ValueError, requests.exceptions.RequestException) as e:
            logger.exception(f"Error getting model names: {e}")
            model_ids = ANTHROPIC_MODELS

        if tool_model_enabled:
            try:
                from langchain_anthropic.chat_models import ChatAnthropic
            except ImportError as e:
                msg = "langchain_anthropic is not installed. Please install it with `pip install langchain_anthropic`."
                raise ImportError(msg) from e

            # Create a new list instead of modifying while iterating
            filtered_models = []
            for model in model_ids:
                if model in TOOL_CALLING_SUPPORTED_ANTHROPIC_MODELS:
                    filtered_models.append(model)
                    continue

                model_with_tool = ChatAnthropic(
                    model=model,  # Use the current model being checked
                    anthropic_api_key=self.api_key,
                    anthropic_api_url=cast("str", self.base_url) or DEFAULT_ANTHROPIC_API_URL,
                )

                if (
                    not self.supports_tool_calling(model_with_tool)
                    or model in TOOL_CALLING_UNSUPPORTED_ANTHROPIC_MODELS
                ):
                    continue

                filtered_models.append(model)

            return filtered_models

        return model_ids