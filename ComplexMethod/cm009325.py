def _set_clients(self) -> Self:
        """Set clients to use for ollama."""
        if self.top_logprobs is not None and self.logprobs is not True:
            if self.logprobs is False:
                msg = (
                    "`top_logprobs` is set but `logprobs` is explicitly `False`. "
                    "Either set `logprobs=True` to use `top_logprobs`, or remove "
                    "`top_logprobs`."
                )
                raise ValueError(msg)
            # logprobs is None (unset) — auto-enable as convenience
            self.logprobs = True
            warnings.warn(
                "`top_logprobs` is set but `logprobs` was not explicitly enabled. "
                "Setting `logprobs=True` automatically.",
                UserWarning,
                stacklevel=2,
            )

        client_kwargs = self.client_kwargs or {}

        cleaned_url, auth_headers = parse_url_with_auth(self.base_url)
        merge_auth_headers(client_kwargs, auth_headers)

        sync_client_kwargs = client_kwargs
        if self.sync_client_kwargs:
            sync_client_kwargs = {**sync_client_kwargs, **self.sync_client_kwargs}

        async_client_kwargs = client_kwargs
        if self.async_client_kwargs:
            async_client_kwargs = {**async_client_kwargs, **self.async_client_kwargs}

        self._client = Client(host=cleaned_url, **sync_client_kwargs)
        self._async_client = AsyncClient(host=cleaned_url, **async_client_kwargs)
        if self.validate_model_on_init:
            validate_model(self._client, self.model)
        return self