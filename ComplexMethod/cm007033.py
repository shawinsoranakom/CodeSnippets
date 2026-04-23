def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        api_key = self.api_key
        temperature = self.temperature
        model_name: str = self.model_name
        max_tokens = self.max_tokens
        model_kwargs = getattr(self, "model_kwargs", {}) or {}
        json_mode = self.json_mode
        seed = self.seed
        # Ensure a valid model was selected
        if not model_name or model_name == "Select a model":
            msg = "Please select a valid CometAPI model."
            raise ValueError(msg)
        try:
            # Extract raw API key safely
            _api_key = api_key.get_secret_value() if isinstance(api_key, SecretStr) else api_key
            output = ChatOpenAI(
                model=model_name,
                api_key=_api_key or None,
                max_tokens=max_tokens or None,
                temperature=temperature,
                model_kwargs=model_kwargs,
                streaming=bool(self.stream),
                seed=seed,
                base_url="https://api.cometapi.com/v1",
            )
        except (TypeError, ValueError) as e:
            msg = "Could not connect to CometAPI."
            raise ValueError(msg) from e

        if json_mode:
            output = output.bind(response_format={"type": "json_object"})

        return output