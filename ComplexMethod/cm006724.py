def _extract_auth_modes_from_schema(self, schema: dict[str, Any] | None) -> list[str]:
        """Return available auth modes (e.g., OAUTH2, API_KEY) from toolkit schema."""
        if not schema:
            return []
        modes: list[str] = []
        # composio_managed_auth_schemes: list[str]
        managed = schema.get("composio_managed_auth_schemes") or schema.get("composioManagedAuthSchemes") or []
        has_managed_schemes = isinstance(managed, list) and len(managed) > 0

        # Add "Composio_Managed" as first option if there are managed schemes
        if has_managed_schemes:
            modes.append("Composio_Managed")

        # auth_config_details: list with entries containing mode
        details = schema.get("auth_config_details") or schema.get("authConfigDetails") or []
        for item in details:
            mode = item.get("mode") or item.get("auth_method")
            if isinstance(mode, str) and mode not in modes:
                modes.append(mode)
        return modes