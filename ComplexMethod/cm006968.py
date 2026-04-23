def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        logger.debug(f"Executing request with model: {self.model_name}")
        # Handle api_key - it can be string or SecretStr
        api_key_value = None
        if self.api_key:
            logger.debug(f"API key type: {type(self.api_key)}, value: {'***' if self.api_key else None}")
            if isinstance(self.api_key, SecretStr):
                api_key_value = self.api_key.get_secret_value()
            else:
                api_key_value = str(self.api_key)
        logger.debug(f"Final api_key_value type: {type(api_key_value)}, value: {'***' if api_key_value else None}")

        # Handle model_kwargs and ensure api_key doesn't conflict
        model_kwargs = self.model_kwargs or {}
        # Remove api_key from model_kwargs if it exists to prevent conflicts
        if "api_key" in model_kwargs:
            logger.warning("api_key found in model_kwargs, removing to prevent conflicts")
            model_kwargs = dict(model_kwargs)  # Make a copy
            del model_kwargs["api_key"]

        parameters = {
            "api_key": api_key_value,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens or None,
            "model_kwargs": model_kwargs,
            "base_url": self.openai_api_base or "https://api.openai.com/v1",
            "max_retries": self.max_retries,
            "timeout": self.timeout,
        }

        # TODO: Revisit if/once parameters are supported for reasoning models
        unsupported_params_for_reasoning_models = ["temperature", "seed"]

        if self.model_name not in OPENAI_REASONING_MODEL_NAMES:
            parameters["temperature"] = self.temperature if self.temperature is not None else 0.1
            parameters["seed"] = self.seed
        else:
            params_str = ", ".join(unsupported_params_for_reasoning_models)
            logger.debug(f"{self.model_name} is a reasoning model, {params_str} are not configurable. Ignoring.")

        # Ensure all parameter values are the correct types
        if isinstance(parameters.get("api_key"), SecretStr):
            parameters["api_key"] = parameters["api_key"].get_secret_value()
        parameters["stream_usage"] = True
        output = ChatOpenAI(**parameters)
        if self.json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output