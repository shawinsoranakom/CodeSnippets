def _async_should_report_integration(
        self,
        integration: Integration,
        yaml_domains: set[str],
        entity_registry_platforms: set[str],
    ) -> bool:
        """Return a bool to indicate if this integration should be reported."""
        if integration.disabled:
            return False

        # Check if the integration is defined in YAML or in the entity registry
        if (
            integration.domain in yaml_domains
            or integration.domain in entity_registry_platforms
        ):
            return True

        # Check if the integration provide a config flow
        if not integration.config_flow:
            return False

        entries = self._hass.config_entries.async_entries(integration.domain)

        # Filter out ignored and disabled entries
        return any(
            entry
            for entry in entries
            if entry.source != SOURCE_IGNORE and entry.disabled_by is None
        )