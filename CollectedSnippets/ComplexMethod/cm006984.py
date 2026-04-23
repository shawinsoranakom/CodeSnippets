def _resolve_selected_model(self):
        """Resolve the selected model, including legacy agent_llm/model_name inputs."""
        try:
            from langchain_core.language_models import BaseLanguageModel

            if isinstance(self.model, BaseLanguageModel):
                return self.model
        except ImportError:
            pass

        if isinstance(self.model, list) and self.model:
            return self.model

        legacy_provider = getattr(self, "agent_llm", None)
        legacy_model_name = getattr(self, "model_name", None)
        if not legacy_provider or not legacy_model_name:
            return self.model

        options = get_language_model_options(user_id=self.user_id)
        for option in options:
            if option.get("provider") == legacy_provider and option.get("name") == legacy_model_name:
                return [option]

        return [
            {
                "name": legacy_model_name,
                "provider": legacy_provider,
                "metadata": {},
            }
        ]