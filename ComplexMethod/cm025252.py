async def async_trigger_cleanup(self) -> None:
        """Trigger device trackers cleanup."""
        _LOGGER.debug("Device tracker cleanup triggered")
        device_hosts = {self.mac: Device(True, "", "", "", "", None)}
        if self.device_discovery_enabled:
            device_hosts = await self._async_update_hosts_info()
        entity_reg: er.EntityRegistry = er.async_get(self.hass)
        config_entry = self.config_entry

        entities: list[er.RegistryEntry] = er.async_entries_for_config_entry(
            entity_reg, config_entry.entry_id
        )
        for entity in entities:
            entry_mac = entity.unique_id.split("_")[0]
            if (
                entity.domain == DEVICE_TRACKER_DOMAIN
                or "_internet_access" in entity.unique_id
            ) and entry_mac not in device_hosts:
                _LOGGER.debug("Removing orphan entity entry %s", entity.entity_id)
                entity_reg.async_remove(entity.entity_id)

        device_reg = dr.async_get(self.hass)
        valid_connections = {
            (CONNECTION_NETWORK_MAC, dr.format_mac(mac)) for mac in device_hosts
        }
        for device in dr.async_entries_for_config_entry(
            device_reg, config_entry.entry_id
        ):
            if not any(con in device.connections for con in valid_connections):
                _LOGGER.debug("Removing obsolete device entry %s", device.name)
                device_reg.async_update_device(
                    device.id, remove_config_entry_id=config_entry.entry_id
                )