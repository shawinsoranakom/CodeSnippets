def _validate_oauth_settings(self, auth_config: dict[str, Any]) -> None:
        """Validate that all required OAuth settings are present and non-empty.

        Raises:
            MCPComposerConfigError: If any required OAuth field is missing or empty
        """
        if auth_config.get("auth_type") != "oauth":
            return

        required_fields = [
            "oauth_host",
            "oauth_port",
            "oauth_server_url",
            "oauth_auth_url",
            "oauth_token_url",
            "oauth_client_id",
            "oauth_client_secret",
        ]

        missing_fields = []
        empty_fields = []

        for field in required_fields:
            value = auth_config.get(field)
            if value is None:
                missing_fields.append(field)
            elif not str(value).strip():
                empty_fields.append(field)

        error_parts = []
        if missing_fields:
            error_parts.append(f"Missing required fields: {', '.join(missing_fields)}")
        if empty_fields:
            error_parts.append(f"Empty required fields: {', '.join(empty_fields)}")

        if error_parts:
            config_error_msg = f"Invalid OAuth configuration: {'; '.join(error_parts)}"
            raise MCPComposerConfigError(config_error_msg)