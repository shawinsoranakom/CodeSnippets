async def _handle_entity_registry_updated(
        self, event: Event[er.EventEntityRegistryUpdatedData]
    ) -> None:
        """Handle when entity registry updated."""
        entity_id = event.data["entity_id"]
        entity_entry: er.RegistryEntry | None = er.async_get(self.hass).async_get(
            entity_id
        )
        if (
            entity_entry is None
            or entity_entry.config_entry_id != self.config_entry.entry_id
            or entity_entry.device_id is None
        ):
            return
        device_entry: dr.DeviceEntry | None = dr.async_get(self.hass).async_get(
            entity_entry.device_id
        )
        assert device_entry

        ieee_address = next(
            identifier
            for domain, identifier in device_entry.identifiers
            if domain == DOMAIN
        )
        assert ieee_address

        ieee = EUI64.convert(ieee_address)

        assert ieee in self.device_proxies

        zha_device_proxy = self.device_proxies[ieee]
        entity_key = (entity_entry.domain, entity_entry.unique_id)
        if entity_key not in zha_device_proxy.device.platform_entities:
            return
        platform_entity = zha_device_proxy.device.platform_entities[entity_key]
        if entity_entry.disabled:
            platform_entity.disable()
        else:
            platform_entity.enable()