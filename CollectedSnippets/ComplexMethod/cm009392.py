def validate_environment(self) -> Self:
        """Validate that api key and python package exists in environment."""
        if self.n < 1:
            msg = "n must be at least 1."
            raise ValueError(msg)
        if self.n > 1 and self.streaming:
            msg = "n must be 1 when streaming."
            raise ValueError(msg)

        client_params = {
            "api_key": (
                self.fireworks_api_key.get_secret_value()
                if self.fireworks_api_key
                else None
            ),
            "base_url": self.fireworks_api_base,
            "timeout": self.request_timeout,
        }

        if not self.client:
            self.client = Fireworks(**client_params).chat.completions
        if not self.async_client:
            self.async_client = AsyncFireworks(**client_params).chat.completions
        if self.max_retries:
            self.client._max_retries = self.max_retries
            self.async_client._max_retries = self.max_retries
        return self