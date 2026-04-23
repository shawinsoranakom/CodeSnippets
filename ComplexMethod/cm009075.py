def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        # For backwards compatibility. Before openai v1, no distinction was made
        # between azure_endpoint and base_url (openai_api_base).
        openai_api_base = self.openai_api_base
        if openai_api_base and self.validate_base_url:
            # Only validate openai_api_base if azure_endpoint is not provided
            if not self.azure_endpoint and "/openai" not in openai_api_base:
                self.openai_api_base = cast(str, self.openai_api_base) + "/openai"
                msg = (
                    "As of openai>=1.0.0, Azure endpoints should be specified via "
                    "the `azure_endpoint` param not `openai_api_base` "
                    "(or alias `base_url`). "
                )
                raise ValueError(msg)
            if self.deployment:
                msg = (
                    "As of openai>=1.0.0, if `deployment` (or alias "
                    "`azure_deployment`) is specified then "
                    "`openai_api_base` (or alias `base_url`) should not be. "
                    "Instead use `deployment` (or alias `azure_deployment`) "
                    "and `azure_endpoint`."
                )
                raise ValueError(msg)
        client_params: dict = {
            "api_version": self.openai_api_version,
            "azure_endpoint": self.azure_endpoint,
            "azure_deployment": self.deployment,
            "api_key": (
                self.openai_api_key.get_secret_value() if self.openai_api_key else None
            ),
            "azure_ad_token": (
                self.azure_ad_token.get_secret_value() if self.azure_ad_token else None
            ),
            "azure_ad_token_provider": self.azure_ad_token_provider,
            "organization": self.openai_organization,
            "base_url": self.openai_api_base,
            "timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "default_headers": {
                "User-Agent": "langchain-partner-python-azure-openai",
                **(self.default_headers or {}),
            },
            "default_query": self.default_query,
        }
        if not self.client:
            sync_specific: dict = {"http_client": self.http_client}
            self.client = openai.AzureOpenAI(
                **client_params,  # type: ignore[arg-type]
                **sync_specific,
            ).embeddings
        if not self.async_client:
            async_specific: dict = {"http_client": self.http_async_client}

            if self.azure_ad_async_token_provider:
                client_params["azure_ad_token_provider"] = (
                    self.azure_ad_async_token_provider
                )

            self.async_client = openai.AsyncAzureOpenAI(
                **client_params,  # type: ignore[arg-type]
                **async_specific,
            ).embeddings
        return self