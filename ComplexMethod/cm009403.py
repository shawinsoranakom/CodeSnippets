def validate_environment(self) -> Self:
        """Validate that package is installed and that the API token is valid."""
        huggingfacehub_api_token = self.huggingfacehub_api_token or os.getenv(
            "HF_TOKEN"
        )
        # Local/custom endpoint URL -> don't pass HF token (avoids 401s and egress).
        if self.endpoint_url and not _is_huggingface_hosted_url(self.endpoint_url):
            client_api_key: str | None = None
        else:
            client_api_key = huggingfacehub_api_token

        from huggingface_hub import (  # type: ignore[import]
            AsyncInferenceClient,  # type: ignore[import]
            InferenceClient,  # type: ignore[import]
        )

        # Instantiate clients with supported kwargs
        sync_supported_kwargs = set(inspect.signature(InferenceClient).parameters)
        self.client = InferenceClient(
            model=self.model,
            timeout=self.timeout,
            api_key=client_api_key,
            provider=self.provider,  # type: ignore[arg-type]
            **{
                key: value
                for key, value in self.server_kwargs.items()
                if key in sync_supported_kwargs
            },
        )

        async_supported_kwargs = set(inspect.signature(AsyncInferenceClient).parameters)
        self.async_client = AsyncInferenceClient(
            model=self.model,
            timeout=self.timeout,
            api_key=client_api_key,
            provider=self.provider,  # type: ignore[arg-type]
            **{
                key: value
                for key, value in self.server_kwargs.items()
                if key in async_supported_kwargs
            },
        )
        ignored_kwargs = (
            set(self.server_kwargs.keys())
            - sync_supported_kwargs
            - async_supported_kwargs
        )
        if len(ignored_kwargs) > 0:
            logger.warning(
                f"Ignoring following parameters as they are not supported by the "
                f"InferenceClient or AsyncInferenceClient: {ignored_kwargs}."
            )

        return self