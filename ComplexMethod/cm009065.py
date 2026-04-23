def validate_environment(self) -> Self:
        """Validate api key, python package exists, temperature, and top_p."""
        if isinstance(self.mistral_api_key, SecretStr):
            api_key_str: str | None = self.mistral_api_key.get_secret_value()
        else:
            api_key_str = self.mistral_api_key

        # TODO: handle retries
        base_url_str = (
            self.endpoint
            or os.environ.get("MISTRAL_BASE_URL")
            or "https://api.mistral.ai/v1"
        )
        self.endpoint = base_url_str
        if not self.client:
            self.client = httpx.Client(
                base_url=base_url_str,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key_str}",
                },
                timeout=self.timeout,
                verify=global_ssl_context,
            )
        # TODO: handle retries and max_concurrency
        if not self.async_client:
            self.async_client = httpx.AsyncClient(
                base_url=base_url_str,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key_str}",
                },
                timeout=self.timeout,
                verify=global_ssl_context,
            )

        if self.temperature is not None and not 0 <= self.temperature <= 1:
            msg = "temperature must be in the range [0.0, 1.0]"
            raise ValueError(msg)

        if self.top_p is not None and not 0 <= self.top_p <= 1:
            msg = "top_p must be in the range [0.0, 1.0]"
            raise ValueError(msg)

        return self