async def _async_process_registry_update_or_remove(
        self, event: Event[er.EventEntityRegistryUpdatedData]
    ) -> None:
        """Handle entity registry update or remove."""
        data = event.data
        if data["action"] == "remove":
            await self.async_removed_from_registry()
            self.registry_entry = None
            await self.async_remove()

        if data["action"] != "update":
            return

        if "device_id" in data["changes"]:
            self._async_subscribe_device_updates()

        # Invalidate friendly name cache if relevant fields changed
        changes = data["changes"]
        if "name" in changes or "has_entity_name" in changes or "device_id" in changes:
            self._cached_friendly_name = None

        ent_reg = er.async_get(self.hass)
        old = self.registry_entry
        registry_entry = ent_reg.async_get(data["entity_id"])
        assert registry_entry is not None
        self.registry_entry = registry_entry

        if device_id := registry_entry.device_id:
            self.device_entry = dr.async_get(self.hass).async_get(device_id)

        if registry_entry.disabled:
            await self.async_remove()
            return

        assert old is not None
        if registry_entry.entity_id == old.entity_id:
            self.async_registry_entry_updated()
            self.async_write_ha_state()
            return

        await self.async_remove(force_remove=True)

        self.entity_id = registry_entry.entity_id

        # Clear the remove future to handle entity added again after entity id change
        self.__remove_future = None
        self._platform_state = EntityPlatformState.NOT_ADDED
        await self.platform.async_add_entities(
            [self], config_subentry_id=registry_entry.config_subentry_id
        )