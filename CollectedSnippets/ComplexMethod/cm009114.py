def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        if self.n is not None and self.n < 1:
            msg = "n must be at least 1."
            raise ValueError(msg)
        if self.n is not None and self.n > 1 and self.streaming:
            msg = "n must be 1 when streaming."
            raise ValueError(msg)

        if self.disabled_params is None:
            # As of 09-17-2024 'parallel_tool_calls' param is only supported for gpt-4o.
            if self.model_name and self.model_name == "gpt-4o":
                pass
            else:
                self.disabled_params = {"parallel_tool_calls": None}

        # Check OPENAI_ORGANIZATION for backwards compatibility.
        self.openai_organization = (
            self.openai_organization
            or os.getenv("OPENAI_ORG_ID")
            or os.getenv("OPENAI_ORGANIZATION")
        )

        # Enable stream_usage by default if using default base URL and client
        if all(
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
        ):
            self.stream_usage = True

        # For backwards compatibility. Before openai v1, no distinction was made
        # between azure_endpoint and base_url (openai_api_base).
        openai_api_base = self.openai_api_base
        if openai_api_base and self.validate_base_url:
            if "/openai" not in openai_api_base:
                msg = (
                    "As of openai>=1.0.0, Azure endpoints should be specified via "
                    "the `azure_endpoint` param not `openai_api_base` "
                    "(or alias `base_url`)."
                )
                raise ValueError(msg)
            if self.deployment_name:
                msg = (
                    "As of openai>=1.0.0, if `azure_deployment` (or alias "
                    "`deployment_name`) is specified then "
                    "`base_url` (or alias `openai_api_base`) should not be. "
                    "If specifying `azure_deployment`/`deployment_name` then use "
                    "`azure_endpoint` instead of `base_url`.\n\n"
                    "For example, you could specify:\n\n"
                    'azure_endpoint="https://xxx.openai.azure.com/", '
                    'azure_deployment="my-deployment"\n\n'
                    "Or you can equivalently specify:\n\n"
                    'base_url="https://xxx.openai.azure.com/openai/deployments/my-deployment"'
                )
                raise ValueError(msg)
        client_params: dict = {
            "api_version": self.openai_api_version,
            "azure_endpoint": self.azure_endpoint,
            "azure_deployment": self.deployment_name,
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
            "default_headers": {
                "User-Agent": "langchain-partner-python-azure-openai",
                **(self.default_headers or {}),
            },
            "default_query": self.default_query,
        }
        if self.max_retries is not None:
            client_params["max_retries"] = self.max_retries

        if not self.client:
            sync_specific = {"http_client": self.http_client}
            self.root_client = openai.AzureOpenAI(**client_params, **sync_specific)  # type: ignore[arg-type]
            self.client = self.root_client.chat.completions
        if not self.async_client:
            async_specific = {"http_client": self.http_async_client}

            if self.azure_ad_async_token_provider:
                client_params["azure_ad_token_provider"] = (
                    self.azure_ad_async_token_provider
                )

            self.root_async_client = openai.AsyncAzureOpenAI(
                **client_params,
                **async_specific,  # type: ignore[arg-type]
            )
            self.async_client = self.root_async_client.chat.completions
        return self