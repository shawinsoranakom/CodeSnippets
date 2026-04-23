async def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None):
        if field_name == "enable_structured_output":  # bind enable_structured_output boolean to format show value
            build_config["format"]["show"] = field_value

        if field_name == "mirostat":
            if field_value == "Disabled":
                build_config["mirostat_eta"]["advanced"] = True
                build_config["mirostat_tau"]["advanced"] = True
                build_config["mirostat_eta"]["value"] = None
                build_config["mirostat_tau"]["value"] = None

            else:
                build_config["mirostat_eta"]["advanced"] = False
                build_config["mirostat_tau"]["advanced"] = False

                if field_value == "Mirostat 2.0":
                    build_config["mirostat_eta"]["value"] = 0.2
                    build_config["mirostat_tau"]["value"] = 10
                else:
                    build_config["mirostat_eta"]["value"] = 0.1
                    build_config["mirostat_tau"]["value"] = 5

        if field_name in {"model_name", "base_url", "tool_model_enabled"}:
            # Use field_value if base_url is being updated, otherwise use self.base_url
            base_url_to_check = field_value if field_name == "base_url" else self.base_url
            # Fallback to self.base_url if field_value is None or empty
            if not base_url_to_check and field_name == "base_url":
                base_url_to_check = self.base_url
            logger.warning(f"Fetching Ollama models from updated URL: {base_url_to_check}")

            if base_url_to_check and await self.is_valid_ollama_url(base_url_to_check):
                tool_model_enabled = build_config["tool_model_enabled"].get("value", False) or self.tool_model_enabled
                build_config["model_name"]["options"] = await self.get_models(
                    base_url_to_check, tool_model_enabled=tool_model_enabled
                )
            else:
                build_config["model_name"]["options"] = []
        if field_name == "keep_alive_flag":
            if field_value == "Keep":
                build_config["keep_alive"]["value"] = "-1"
                build_config["keep_alive"]["advanced"] = True
            elif field_value == "Immediately":
                build_config["keep_alive"]["value"] = "0"
                build_config["keep_alive"]["advanced"] = True
            else:
                build_config["keep_alive"]["advanced"] = False

        return build_config