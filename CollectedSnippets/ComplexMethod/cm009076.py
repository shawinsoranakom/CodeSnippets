def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        if self.n < 1:
            msg = "n must be at least 1."
            raise ValueError(msg)
        if self.streaming and self.n > 1:
            msg = "Cannot stream results when n > 1."
            raise ValueError(msg)
        if self.streaming and self.best_of > 1:
            msg = "Cannot stream results when best_of > 1."
            raise ValueError(msg)

        # Resolve API key from SecretStr or Callable
        api_key_value: str | Callable[[], str] | None = None
        if self.openai_api_key is not None:
            if isinstance(self.openai_api_key, SecretStr):
                api_key_value = self.openai_api_key.get_secret_value()
            elif callable(self.openai_api_key):
                api_key_value = self.openai_api_key

        client_params: dict = {
            "api_key": api_key_value,
            "organization": self.openai_organization,
            "base_url": self.openai_api_base,
            "timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "default_headers": self.default_headers,
            "default_query": self.default_query,
        }
        if not self.client:
            sync_specific = {"http_client": self.http_client}
            self.client = openai.OpenAI(**client_params, **sync_specific).completions  # type: ignore[arg-type]
        if not self.async_client:
            async_specific = {"http_client": self.http_async_client}
            self.async_client = openai.AsyncOpenAI(
                **client_params,
                **async_specific,  # type: ignore[arg-type]
            ).completions

        return self