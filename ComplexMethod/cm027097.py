async def async_sensors_discovered(
        sensors: list[tuple[TasmotaBaseSensorConfig, DiscoveryHashType]], mac: str
    ) -> None:
        """Handle discovery of (additional) sensors."""
        platform = sensor.DOMAIN

        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        device = device_registry.async_get_device(
            connections={(dr.CONNECTION_NETWORK_MAC, mac)}
        )

        if device is None:
            _LOGGER.warning("Got sensors for unknown device mac: %s", mac)
            return

        orphaned_entities = {
            entry.unique_id
            for entry in async_entries_for_device(
                entity_registry, device.id, include_disabled_entities=True
            )
            if entry.domain == sensor.DOMAIN and entry.platform == DOMAIN
        }
        for tasmota_sensor_config, discovery_hash in sensors:
            if tasmota_sensor_config:
                orphaned_entities.discard(tasmota_sensor_config.unique_id)
            _discover_entity(tasmota_sensor_config, discovery_hash, platform)
        for unique_id in orphaned_entities:
            entity_id = entity_registry.async_get_entity_id(platform, DOMAIN, unique_id)
            if entity_id:
                _LOGGER.debug("Removing entity: %s %s", platform, entity_id)
                entity_registry.async_remove(entity_id)