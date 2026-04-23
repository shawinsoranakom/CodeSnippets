def matches(
        self, hass: HomeAssistant, entity_id: str, domain: str, integration: str
    ) -> bool:
        """Return if entity matches all criteria in this filter."""
        if self.integration and integration != self.integration:
            return False

        if self.domains and domain not in self.domains:
            return False

        if self.device_classes:
            if (
                entity_device_class := get_device_class(hass, entity_id)
            ) is None or entity_device_class not in self.device_classes:
                return False

        if self.supported_features:
            entity_supported_features = get_supported_features(hass, entity_id)
            if not any(
                feature & entity_supported_features == feature
                for feature in self.supported_features
            ):
                return False

        return True