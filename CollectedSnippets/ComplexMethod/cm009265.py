def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        if self.n is not None and self.n < 1:
            msg = "n must be at least 1."
            raise ValueError(msg)
        if self.n is not None and self.n > 1 and self.streaming:
            msg = "n must be 1 when streaming."
            raise ValueError(msg)

        client_params: dict = {
            "api_key": (
                self.xai_api_key.get_secret_value() if self.xai_api_key else None
            ),
            "base_url": self.xai_api_base,
            "timeout": self.request_timeout,
            "default_headers": self.default_headers,
            "default_query": self.default_query,
        }
        if self.max_retries is not None:
            client_params["max_retries"] = self.max_retries

        if client_params["api_key"] is None:
            msg = (
                "xAI API key is not set. Please set it in the `xai_api_key` field or "
                "in the `XAI_API_KEY` environment variable."
            )
            raise ValueError(msg)

        if not (self.client or None):
            sync_specific: dict = {"http_client": self.http_client}
            self.client = openai.OpenAI(
                **client_params, **sync_specific
            ).chat.completions
            self.root_client = openai.OpenAI(**client_params, **sync_specific)
        if not (self.async_client or None):
            async_specific: dict = {"http_client": self.http_async_client}
            self.async_client = openai.AsyncOpenAI(
                **client_params, **async_specific
            ).chat.completions
            self.root_async_client = openai.AsyncOpenAI(
                **client_params,
                **async_specific,
            )

        # Enable streaming usage metadata by default
        if self.stream_usage is not False:
            self.stream_usage = True

        return self