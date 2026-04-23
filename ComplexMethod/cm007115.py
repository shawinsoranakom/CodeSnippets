async def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None):
        if field_name in {"base_url", "model_name"} and not await self.is_valid_ollama_url(self.base_url):
            msg = "Ollama is not running on the provided base URL. Please start Ollama and try again."
            raise ValueError(msg)
        if field_name in {"model_name", "base_url"}:
            # Use field_value if base_url is being updated, otherwise use self.base_url
            base_url_to_check = field_value if field_name == "base_url" else self.base_url
            # Fallback to self.base_url if field_value is None or empty
            if not base_url_to_check and field_name == "base_url":
                base_url_to_check = self.base_url
            logger.warning(f"Fetching Ollama models from updated URL: {base_url_to_check}")

            if base_url_to_check and await self.is_valid_ollama_url(base_url_to_check):
                build_config["model_name"]["options"] = await self.get_model(base_url_to_check)
            else:
                build_config["model_name"]["options"] = []

        return build_config