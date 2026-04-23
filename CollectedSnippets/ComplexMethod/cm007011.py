def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        logger.debug(f"Executing request with vLLM model: {self.model_name}")
        parameters = {
            "api_key": SecretStr(self.api_key).get_secret_value() if self.api_key else None,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens or None,
            "model_kwargs": self.model_kwargs or {},
            "base_url": self.api_base or "http://localhost:8000/v1",
            "temperature": self.temperature if self.temperature is not None else 0.1,
        }

        # Only add optional parameters if explicitly set (not -1)
        if self.seed is not None and self.seed != -1:
            parameters["seed"] = self.seed
        if self.timeout is not None and self.timeout != -1:
            parameters["timeout"] = self.timeout
        if self.max_retries is not None and self.max_retries != -1:
            parameters["max_retries"] = self.max_retries

        output = ChatOpenAI(**parameters)
        if self.json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output