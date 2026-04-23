def _has_auth_config_changed(self, existing_auth: dict[str, Any] | None, new_auth: dict[str, Any] | None) -> bool:
        """Check if auth configuration has changed in a way that requires restart."""
        if not existing_auth and not new_auth:
            return False

        if not existing_auth or not new_auth:
            return True

        existing_auth = self._normalize_oauth_callback_aliases(existing_auth)
        new_auth = self._normalize_oauth_callback_aliases(new_auth)

        auth_type = new_auth.get("auth_type", "")

        # Auth type changed?
        if existing_auth.get("auth_type") != auth_type:
            return True

        # Define which fields to check for each auth type
        fields_to_check = []
        if auth_type == "oauth":
            # Get all oauth_* fields plus host/port from both configs
            all_keys = set(existing_auth.keys()) | set(new_auth.keys())
            fields_to_check = [k for k in all_keys if k.startswith("oauth_") or k in ["host", "port"]]
        elif auth_type == "apikey":
            fields_to_check = ["api_key"]

        # Compare relevant fields
        for field in fields_to_check:
            old_normalized = self._normalize_config_value(existing_auth.get(field))
            new_normalized = self._normalize_config_value(new_auth.get(field))

            if old_normalized != new_normalized:
                return True

        return False