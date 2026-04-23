def validate_temperature(cls, values: dict[str, Any]) -> Any:
        """Validate temperature parameter for different models.

        - gpt-5 models (excluding gpt-5-chat) only allow `temperature=1` or unset
            (Defaults to 1)
        """
        model = values.get("model_name") or values.get("model") or ""
        model_lower = model.lower()

        # For o1 models, set temperature=1 if not provided
        if model_lower.startswith("o1") and "temperature" not in values:
            values["temperature"] = 1

        # For gpt-5 models, handle temperature restrictions. Temperature is supported
        # by gpt-5-chat and gpt-5 models with reasoning_effort='none' or
        # reasoning={'effort': 'none'}.
        if (
            model_lower.startswith("gpt-5")
            and ("chat" not in model_lower)
            and values.get("reasoning_effort") != "none"
            and (values.get("reasoning") or {}).get("effort") != "none"
        ):
            temperature = values.get("temperature")
            if temperature is not None and temperature != 1:
                # For gpt-5 (non-chat), only temperature=1 is supported
                # So we remove any non-defaults
                values.pop("temperature", None)

        return values