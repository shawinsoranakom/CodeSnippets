def _is_default_exposed(
        self, entity_id: str, registry_entry: er.RegistryEntry | None
    ) -> bool:
        """Return True if an entity is exposed by default."""
        if registry_entry and (
            registry_entry.entity_category is not None
            or registry_entry.hidden_by is not None
        ):
            return False

        domain = split_entity_id(entity_id)[0]
        if domain in DEFAULT_EXPOSED_DOMAINS:
            return True

        try:
            device_class = get_device_class(self._hass, entity_id)
        except HomeAssistantError:
            # The entity no longer exists
            return False
        if (
            domain == "binary_sensor"
            and device_class in DEFAULT_EXPOSED_BINARY_SENSOR_DEVICE_CLASSES
        ):
            return True

        if domain == "sensor" and device_class in DEFAULT_EXPOSED_SENSOR_DEVICE_CLASSES:
            return True

        return False