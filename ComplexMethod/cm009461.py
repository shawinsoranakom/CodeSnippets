def _get_ls_params(
        self,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> LangSmithParams:
        """Get standard params for tracing."""
        # get default provider from class name
        default_provider = self.__class__.__name__
        if default_provider.startswith("Chat"):
            default_provider = default_provider[4:].lower()
        elif default_provider.endswith("Chat"):
            default_provider = default_provider[:-4]
        default_provider = default_provider.lower()

        ls_params = LangSmithParams(ls_provider=default_provider, ls_model_type="chat")
        if stop:
            ls_params["ls_stop"] = stop

        # model
        if "model" in kwargs and isinstance(kwargs["model"], str):
            ls_params["ls_model_name"] = kwargs["model"]
        elif hasattr(self, "model") and isinstance(self.model, str):
            ls_params["ls_model_name"] = self.model
        elif hasattr(self, "model_name") and isinstance(self.model_name, str):
            ls_params["ls_model_name"] = self.model_name

        # temperature
        if "temperature" in kwargs and isinstance(kwargs["temperature"], (int, float)):
            ls_params["ls_temperature"] = kwargs["temperature"]
        elif hasattr(self, "temperature") and isinstance(
            self.temperature, (int, float)
        ):
            ls_params["ls_temperature"] = self.temperature

        # max_tokens
        if "max_tokens" in kwargs and isinstance(kwargs["max_tokens"], int):
            ls_params["ls_max_tokens"] = kwargs["max_tokens"]
        elif hasattr(self, "max_tokens") and isinstance(self.max_tokens, int):
            ls_params["ls_max_tokens"] = self.max_tokens

        return ls_params