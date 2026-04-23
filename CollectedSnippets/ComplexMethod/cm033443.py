def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("Firecrawl API key is required")

        if not self.api_key.startswith("fc-"):
            raise ValueError("Invalid Firecrawl API key format. Must start with 'fc-'")

        if self.max_retries < 1 or self.max_retries > 10:
            raise ValueError("Max retries must be between 1 and 10")

        if self.timeout < 5 or self.timeout > 300:
            raise ValueError("Timeout must be between 5 and 300 seconds")

        if self.rate_limit_delay < 0.1 or self.rate_limit_delay > 10.0:
            raise ValueError("Rate limit delay must be between 0.1 and 10.0 seconds")