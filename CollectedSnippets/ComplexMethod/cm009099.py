def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        if self.n is not None and self.n < 1:
            msg = "n must be at least 1."
            raise ValueError(msg)
        if self.n is not None and self.n > 1 and self.streaming:
            msg = "n must be 1 when streaming."
            raise ValueError(msg)

        # Check OPENAI_ORGANIZATION for backwards compatibility.
        self.openai_organization = (
            self.openai_organization
            or os.getenv("OPENAI_ORG_ID")
            or os.getenv("OPENAI_ORGANIZATION")
        )
        self.openai_api_base = self.openai_api_base or os.getenv("OPENAI_API_BASE")

        # Enable stream_usage by default if using default base URL and client
        if (
            all(
                getattr(self, key, None) is None
                for key in (
                    "stream_usage",
                    "openai_proxy",
                    "openai_api_base",
                    "base_url",
                    "client",
                    "root_client",
                    "async_client",
                    "root_async_client",
                    "http_client",
                    "http_async_client",
                )
            )
            and "OPENAI_BASE_URL" not in os.environ
        ):
            self.stream_usage = True

        # Resolve API key from SecretStr or Callable
        sync_api_key_value: str | Callable[[], str] | None = None
        async_api_key_value: str | Callable[[], Awaitable[str]] | None = None

        if self.openai_api_key is not None:
            # Because OpenAI and AsyncOpenAI clients support either sync or async
            # callables for the API key, we need to resolve separate values here.
            sync_api_key_value, async_api_key_value = _resolve_sync_and_async_api_keys(
                self.openai_api_key
            )

        client_params: dict = {
            "organization": self.openai_organization,
            "base_url": self.openai_api_base,
            "timeout": self.request_timeout,
            "default_headers": self.default_headers,
            "default_query": self.default_query,
        }
        if self.max_retries is not None:
            client_params["max_retries"] = self.max_retries

        if self.openai_proxy and (self.http_client or self.http_async_client):
            openai_proxy = self.openai_proxy
            http_client = self.http_client
            http_async_client = self.http_async_client
            msg = (
                "Cannot specify 'openai_proxy' if one of "
                "'http_client'/'http_async_client' is already specified. Received:\n"
                f"{openai_proxy=}\n{http_client=}\n{http_async_client=}"
            )
            raise ValueError(msg)
        if _should_bypass_socket_options_for_proxy_env(
            http_socket_options=self.http_socket_options,
            http_client=self.http_client,
            http_async_client=self.http_async_client,
            openai_proxy=self.openai_proxy,
        ):
            # Default-shape construction + proxy env var visible to httpx:
            # skip the custom transport so httpx's env-proxy auto-detection
            # still applies. Users who want kernel-level TCP tuning alongside
            # an env proxy can opt in explicitly via `http_socket_options`.
            resolved_socket_options: tuple[tuple[int, int, int], ...] = ()
            _log_proxy_env_bypass_once()
        else:
            resolved_socket_options = _resolve_socket_options(self.http_socket_options)
            _warn_if_proxy_env_shadowed(
                resolved_socket_options, openai_proxy=self.openai_proxy
            )
        if not self.client:
            if sync_api_key_value is None:
                # No valid sync API key, leave client as None and raise informative
                # error on invocation.
                self.client = None
                self.root_client = None
            else:
                if self.openai_proxy and not self.http_client:
                    self.http_client = _build_proxied_sync_httpx_client(
                        proxy=self.openai_proxy,
                        verify=global_ssl_context,
                        socket_options=resolved_socket_options,
                    )
                sync_specific = {
                    "http_client": self.http_client
                    or _get_default_httpx_client(
                        self.openai_api_base,
                        self.request_timeout,
                        resolved_socket_options,
                    ),
                    "api_key": sync_api_key_value,
                }
                self.root_client = openai.OpenAI(**client_params, **sync_specific)  # type: ignore[arg-type]
                self.client = self.root_client.chat.completions
        if not self.async_client:
            if self.openai_proxy and not self.http_async_client:
                self.http_async_client = _build_proxied_async_httpx_client(
                    proxy=self.openai_proxy,
                    verify=global_ssl_context,
                    socket_options=resolved_socket_options,
                )
            async_specific = {
                "http_client": self.http_async_client
                or _get_default_async_httpx_client(
                    self.openai_api_base,
                    self.request_timeout,
                    resolved_socket_options,
                ),
                "api_key": async_api_key_value,
            }
            self.root_async_client = openai.AsyncOpenAI(
                **client_params,
                **async_specific,  # type: ignore[arg-type]
            )
            self.async_client = self.root_async_client.chat.completions
        return self