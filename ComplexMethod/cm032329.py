def validate_config(self, config: dict) -> tuple[bool, Optional[str]]:
        """
        Validate self-managed provider configuration.

        Performs custom validation beyond the basic schema validation,
        such as checking URL format.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate endpoint URL format
        endpoint = config.get("endpoint", "")
        if endpoint:
            # Check if it's a valid HTTP/HTTPS URL or localhost
            import re
            url_pattern = r'^(https?://|http://localhost|http://[\d\.]+:[a-z]+:[/]|http://[\w\.]+:)'
            if not re.match(url_pattern, endpoint):
                return False, f"Invalid endpoint format: {endpoint}. Must start with http:// or https://"

        # Validate pool_size is positive
        pool_size = config.get("pool_size", 10)
        if isinstance(pool_size, int) and pool_size <= 0:
            return False, "Pool size must be greater than 0"

        # Validate timeout is reasonable
        timeout = config.get("timeout", 30)
        if isinstance(timeout, int) and (timeout < 1 or timeout > 600):
            return False, "Timeout must be between 1 and 600 seconds"

        # Validate max_retries
        max_retries = config.get("max_retries", 3)
        if isinstance(max_retries, int) and (max_retries < 0 or max_retries > 10):
            return False, "Max retries must be between 0 and 10"

        return True, None