def _build_client(self) -> Any:
        """Build and return an `openrouter.OpenRouter` SDK client.

        Returns:
            An `openrouter.OpenRouter` SDK client instance.
        """
        import openrouter  # noqa: PLC0415
        from openrouter.utils import (  # noqa: PLC0415
            BackoffStrategy,
            RetryConfig,
        )

        client_kwargs: dict[str, Any] = {
            "api_key": self.openrouter_api_key.get_secret_value(),  # type: ignore[union-attr]
        }
        if self.openrouter_api_base:
            client_kwargs["server_url"] = self.openrouter_api_base
        extra_headers: dict[str, str] = {}
        if self.app_url:
            extra_headers["HTTP-Referer"] = self.app_url
        if self.app_title:
            extra_headers["X-Title"] = self.app_title
        if self.app_categories:
            extra_headers["X-OpenRouter-Categories"] = ",".join(self.app_categories)
        if extra_headers:
            import httpx  # noqa: PLC0415

            client_kwargs["client"] = httpx.Client(
                headers=extra_headers, follow_redirects=True
            )
            client_kwargs["async_client"] = httpx.AsyncClient(
                headers=extra_headers, follow_redirects=True
            )
        if self.request_timeout is not None:
            client_kwargs["timeout_ms"] = self.request_timeout
        if self.max_retries > 0:
            client_kwargs["retry_config"] = RetryConfig(
                strategy="backoff",
                backoff=BackoffStrategy(
                    initial_interval=500,
                    max_interval=60000,
                    exponent=1.5,
                    max_elapsed_time=self.max_retries * 150_000,
                ),
                retry_connection_errors=True,
            )
        return openrouter.OpenRouter(**client_kwargs)