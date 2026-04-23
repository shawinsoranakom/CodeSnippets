def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        if "base_url" in build_config and build_config["base_url"]["value"] is None:
            build_config["base_url"]["value"] = DEFAULT_ANTHROPIC_API_URL
            self.base_url = DEFAULT_ANTHROPIC_API_URL
        if field_name in {"base_url", "model_name", "tool_model_enabled", "api_key"} and field_value:
            try:
                if len(self.api_key) == 0:
                    ids = ANTHROPIC_MODELS
                else:
                    try:
                        ids = self.get_models(tool_model_enabled=self.tool_model_enabled)
                    except (ImportError, ValueError, requests.exceptions.RequestException) as e:
                        logger.exception(f"Error getting model names: {e}")
                        ids = ANTHROPIC_MODELS
                build_config.setdefault("model_name", {})
                build_config["model_name"]["options"] = ids
                build_config["model_name"].setdefault("value", ids[0])
                build_config["model_name"]["combobox"] = True
            except Exception as e:
                msg = f"Error getting model names: {e}"
                raise ValueError(msg) from e
        return build_config