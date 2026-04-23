def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        if field_name in {"base_url", "model_name", "api_key"} and field_value in OPENAI_REASONING_MODEL_NAMES:
            build_config["temperature"]["show"] = False
            build_config["seed"]["show"] = False
            # Hide system_message for o1 models - currently unsupported
            if field_value.startswith("o1") and "system_message" in build_config:
                build_config["system_message"]["show"] = False
        if field_name in {"base_url", "model_name", "api_key"} and field_value in OPENAI_CHAT_MODEL_NAMES:
            build_config["temperature"]["show"] = True
            build_config["seed"]["show"] = True
            if "system_message" in build_config:
                build_config["system_message"]["show"] = True
        return build_config