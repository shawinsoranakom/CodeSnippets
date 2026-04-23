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
        # For backwards compatibility. Before openai v1, no distinction was made
        # between azure_endpoint and base_url (openai_api_base).
        openai_api_base = self.openai_api_base
        if openai_api_base and self.validate_base_url:
            if "/openai" not in openai_api_base:
                self.openai_api_base = (
                    cast(str, self.openai_api_base).rstrip("/") + "/openai"
                )
                msg = (
                    "As of openai>=1.0.0, Azure endpoints should be specified via "
                    "the `azure_endpoint` param not `openai_api_base` "
                    "(or alias `base_url`)."
                )
                raise ValueError(msg)
            if self.deployment_name:
                msg = (
                    "As of openai>=1.0.0, if `deployment_name` (or alias "
                    "`azure_deployment`) is specified then "
                    "`openai_api_base` (or alias `base_url`) should not be. "
                    "Instead use `deployment_name` (or alias `azure_deployment`) "
                    "and `azure_endpoint`."
                )
                raise ValueError(msg)
                self.deployment_name = None
        client_params: dict = {
            "api_version": self.openai_api_version,
            "azure_endpoint": self.azure_endpoint,
            "azure_deployment": self.deployment_name,
            "api_key": self.openai_api_key.get_secret_value()
            if self.openai_api_key
            else None,
            "azure_ad_token": self.azure_ad_token.get_secret_value()
            if self.azure_ad_token
            else None,
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
            sync_specific = {"http_client": self.http_client}
            self.client = openai.AzureOpenAI(
                **client_params,
                **sync_specific,  # type: ignore[arg-type]
            ).completions
        if not self.async_client:
            async_specific = {"http_client": self.http_async_client}

            if self.azure_ad_async_token_provider:
                client_params["azure_ad_token_provider"] = (
                    self.azure_ad_async_token_provider
                )

            self.async_client = openai.AsyncAzureOpenAI(
                **client_params,
                **async_specific,  # type: ignore[arg-type]
            ).completions

        return self