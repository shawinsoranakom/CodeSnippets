def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the provider with configuration.

        Args:
            config: Configuration dictionary with keys:
                - endpoint: HTTP endpoint (default: "http://localhost:9385")
                - timeout: Request timeout in seconds (default: 30)
                - max_retries: Maximum retry attempts (default: 3)
                - pool_size: Container pool size for info (default: 10)

        Returns:
            True if initialization successful, False otherwise
        """
        self.endpoint = config.get("endpoint", "http://localhost:9385")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.pool_size = config.get("pool_size", 10)

        # Validate endpoint is accessible
        if not self.health_check():
            # Try to fall back to SANDBOX_HOST from settings if we are using localhost
            if "localhost" in self.endpoint or "127.0.0.1" in self.endpoint:
                try:
                    from common import settings
                    if settings.SANDBOX_HOST and settings.SANDBOX_HOST not in self.endpoint:
                        original_endpoint = self.endpoint
                        self.endpoint = f"http://{settings.SANDBOX_HOST}:9385"
                        if self.health_check():
                            import logging
                            logging.warning(f"Sandbox self_managed: Connected using settings.SANDBOX_HOST fallback: {self.endpoint} (original: {original_endpoint})")
                            self._initialized = True
                            return True
                        else:
                            self.endpoint = original_endpoint # Restore if fallback also fails
                except ImportError:
                    pass

            return False

        self._initialized = True
        return True