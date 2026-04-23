def validate_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration and return any errors."""
        errors = {}

        # Validate API key
        api_key = config_dict.get("api_key", "")
        if not api_key:
            errors["api_key"] = "API key is required"
        elif not api_key.startswith("fc-"):
            errors["api_key"] = "API key must start with 'fc-'"

        # Validate API URL
        api_url = config_dict.get("api_url", "https://api.firecrawl.dev")
        if not api_url.startswith("http"):
            errors["api_url"] = "API URL must start with http:// or https://"

        # Validate numeric fields
        try:
            max_retries = int(config_dict.get("max_retries", 3))
            if max_retries < 1 or max_retries > 10:
                errors["max_retries"] = "Max retries must be between 1 and 10"
        except (ValueError, TypeError):
            errors["max_retries"] = "Max retries must be a valid integer"

        try:
            timeout = int(config_dict.get("timeout", 30))
            if timeout < 5 or timeout > 300:
                errors["timeout"] = "Timeout must be between 5 and 300 seconds"
        except (ValueError, TypeError):
            errors["timeout"] = "Timeout must be a valid integer"

        try:
            rate_limit_delay = float(config_dict.get("rate_limit_delay", 1.0))
            if rate_limit_delay < 0.1 or rate_limit_delay > 10.0:
                errors["rate_limit_delay"] = "Rate limit delay must be between 0.1 and 10.0 seconds"
        except (ValueError, TypeError):
            errors["rate_limit_delay"] = "Rate limit delay must be a valid number"

        return errors