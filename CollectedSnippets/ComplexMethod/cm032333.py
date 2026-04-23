def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate Aliyun-specific configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate access key format
        access_key_id = config.get("access_key_id", "")
        if access_key_id and not access_key_id.startswith("LTAI"):
            return False, "Invalid AccessKey ID format (should start with 'LTAI')"

        # Validate account ID
        account_id = config.get("account_id", "")
        if not account_id:
            return False, "Account ID is required"

        # Validate region
        valid_regions = ["cn-hangzhou", "cn-beijing", "cn-shanghai", "cn-shenzhen", "cn-guangzhou"]
        region = config.get("region", "cn-hangzhou")
        if region and region not in valid_regions:
            return False, f"Invalid region. Must be one of: {', '.join(valid_regions)}"

        # Validate timeout range (max 30 seconds)
        timeout = config.get("timeout", 30)
        if isinstance(timeout, int) and (timeout < 1 or timeout > 30):
            return False, "Timeout must be between 1 and 30 seconds"

        return True, None