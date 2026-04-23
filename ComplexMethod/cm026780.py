def _async_resolve_up_entity(self, entity_id: str) -> er.RegistryEntry | None:
        """Resolve up from an entity.

        Above an entity is a device, area or floor.
        Above an entity is also the config entry.
        """
        if entity_entry := self._entity_registry.async_get(entity_id):
            # Entity has an overridden area
            if entity_entry.area_id:
                self._add(ItemType.AREA, entity_entry.area_id)
                self._async_resolve_up_area(entity_entry.area_id)

            # Inherit area from device
            elif entity_entry.device_id and (
                device_entry := self._device_registry.async_get(entity_entry.device_id)
            ):
                if device_entry.area_id:
                    self._add(ItemType.AREA, device_entry.area_id)
                    self._async_resolve_up_area(device_entry.area_id)

            # Add device that provided this entity
            self._add(ItemType.DEVICE, entity_entry.device_id)

            # Add config entry that provided this entity
            if entity_entry.config_entry_id:
                self._add(ItemType.CONFIG_ENTRY, entity_entry.config_entry_id)

                if entry := self.hass.config_entries.async_get_entry(
                    entity_entry.config_entry_id
                ):
                    # Add integration that provided this entity
                    self._add(ItemType.INTEGRATION, entry.domain)

        elif source := self._entity_sources.get(entity_id):
            # Add config entry that provided this entity
            self._add(ItemType.CONFIG_ENTRY, source.get("config_entry"))
            self._add(ItemType.INTEGRATION, source["domain"])

        return entity_entry