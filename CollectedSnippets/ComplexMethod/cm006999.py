def _get_model_specs_dict(self, langflow_model_name: str) -> dict[str, Any]:
        """Get a dictionary of relevant model specifications for a given Langflow model name."""
        if not self.use_openrouter_specs or not self._models_api_cache:
            return {
                "id": langflow_model_name,
                "name": langflow_model_name,
                "description": "Specifications not available.",
            }

        api_model_id = self._get_api_model_id_for_langflow_model(langflow_model_name)

        if not api_model_id or api_model_id not in self._models_api_cache:
            log_msg = (
                f"No cached API data found for Langflow model '{langflow_model_name}' "
                f"(mapped API ID: {api_model_id}). Returning basic info."
            )
            self.log(log_msg)
            return {
                "id": langflow_model_name,
                "name": langflow_model_name,
                "description": "Full specifications not found in cache.",
            }

        model_data = self._models_api_cache[api_model_id]
        top_provider_data = model_data.get("top_provider", {})
        architecture_data = model_data.get("architecture", {})
        pricing_data = model_data.get("pricing", {})
        description = model_data.get("description", "No description available")
        truncated_description = (
            description[: self.MAX_DESCRIPTION_LENGTH - 3] + "..."
            if len(description) > self.MAX_DESCRIPTION_LENGTH
            else description
        )

        specs = {
            "id": model_data.get("id"),
            "name": model_data.get("name"),
            "description": truncated_description,
            "context_length": top_provider_data.get("context_length") or model_data.get("context_length"),
            "max_completion_tokens": (
                top_provider_data.get("max_completion_tokens") or model_data.get("max_completion_tokens")
            ),
            "tokenizer": architecture_data.get("tokenizer"),
            "input_modalities": architecture_data.get("input_modalities", []),
            "output_modalities": architecture_data.get("output_modalities", []),
            "pricing_prompt": pricing_data.get("prompt"),
            "pricing_completion": pricing_data.get("completion"),
            "is_moderated": top_provider_data.get("is_moderated"),
            "supported_parameters": model_data.get("supported_parameters", []),
        }
        return {k: v for k, v in specs.items() if v is not None}