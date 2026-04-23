def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        if self.n < 1:
            msg = "n must be at least 1."
            raise ValueError(msg)
        if self.n > 1 and self.streaming:
            msg = "n must be 1 when streaming."
            raise ValueError(msg)
        if self.temperature == 0:
            self.temperature = 1e-8

        default_headers = {"User-Agent": f"langchain/{__version__}"} | dict(
            self.default_headers or {}
        )

        client_params: dict[str, Any] = {
            "api_key": (
                self.groq_api_key.get_secret_value() if self.groq_api_key else None
            ),
            "base_url": self.groq_api_base,
            "timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "default_headers": default_headers,
            "default_query": self.default_query,
        }

        try:
            import groq  # noqa: PLC0415

            sync_specific: dict[str, Any] = {"http_client": self.http_client}
            if not self.client:
                self.client = groq.Groq(
                    **client_params, **sync_specific
                ).chat.completions
            if not self.async_client:
                async_specific: dict[str, Any] = {"http_client": self.http_async_client}
                self.async_client = groq.AsyncGroq(
                    **client_params, **async_specific
                ).chat.completions
        except ImportError as exc:
            msg = (
                "Could not import groq python package. "
                "Please install it with `pip install groq`."
            )
            raise ImportError(msg) from exc
        return self