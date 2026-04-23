def _default_params(self) -> dict[str, Any]:  # noqa: C901, PLR0912
        """Get the default parameters for calling OpenRouter API."""
        params: dict[str, Any] = {
            "model": self.model_name,
            "stream": self.streaming,
            **self.model_kwargs,
        }
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        if self.max_completion_tokens is not None:
            params["max_completion_tokens"] = self.max_completion_tokens
        if self.top_p is not None:
            params["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            params["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            params["presence_penalty"] = self.presence_penalty
        if self.seed is not None:
            params["seed"] = self.seed
        if self.n > 1:
            params["n"] = self.n
        if self.stop is not None:
            params["stop"] = self.stop
        # OpenRouter-specific params
        if self.reasoning is not None:
            params["reasoning"] = self.reasoning
        if self.openrouter_provider is not None:
            params["provider"] = self.openrouter_provider
        if self.route is not None:
            params["route"] = self.route
        if self.plugins is not None:
            params["plugins"] = self.plugins
        return params