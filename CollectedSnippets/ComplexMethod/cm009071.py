def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        if self.openai_api_type in ("azure", "azure_ad", "azuread"):
            msg = (
                "If you are using Azure, please use the `AzureOpenAIEmbeddings` class."
            )
            raise ValueError(msg)

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
            "max_retries": self.max_retries,
            "default_headers": self.default_headers,
            "default_query": self.default_query,
        }

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
        if not self.client:
            if sync_api_key_value is None:
                # No valid sync API key, leave client as None and raise informative
                # error on invocation.
                self.client = None
            else:
                if self.openai_proxy and not self.http_client:
                    try:
                        import httpx
                    except ImportError as e:
                        msg = (
                            "Could not import httpx python package. "
                            "Please install it with `pip install httpx`."
                        )
                        raise ImportError(msg) from e
                    self.http_client = httpx.Client(proxy=self.openai_proxy)
                sync_specific = {
                    "http_client": self.http_client,
                    "api_key": sync_api_key_value,
                }
                self.client = openai.OpenAI(**client_params, **sync_specific).embeddings  # type: ignore[arg-type]
        if not self.async_client:
            if self.openai_proxy and not self.http_async_client:
                try:
                    import httpx
                except ImportError as e:
                    msg = (
                        "Could not import httpx python package. "
                        "Please install it with `pip install httpx`."
                    )
                    raise ImportError(msg) from e
                self.http_async_client = httpx.AsyncClient(proxy=self.openai_proxy)
            async_specific = {
                "http_client": self.http_async_client,
                "api_key": async_api_key_value,
            }
            self.async_client = openai.AsyncOpenAI(
                **client_params,
                **async_specific,  # type: ignore[arg-type]
            ).embeddings
        return self