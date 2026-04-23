async def async_internal_added_to_hass(self) -> None:
        """Handle added to Home Assistant."""
        # Entities without a unique ID don't have a device
        if (
            not self.registry_entry
            or not self.platform.config_entry
            or not self.mac_address
            or (device_entry := self.find_device_entry()) is None
            # Entities should not have a device info. We opt them out
            # of this logic if they do.
            or self.device_info
        ):
            if self.device_info:
                LOGGER.debug("Entity %s unexpectedly has a device info", self.entity_id)
            await super().async_internal_added_to_hass()
            return

        # Attach entry to device
        if self.registry_entry.device_id != device_entry.id:
            self.registry_entry = er.async_get(self.hass).async_update_entity(
                self.entity_id, device_id=device_entry.id
            )

        # Attach device to config entry
        if self.platform.config_entry.entry_id not in device_entry.config_entries:
            dr.async_get(self.hass).async_update_device(
                device_entry.id,
                add_config_entry_id=self.platform.config_entry.entry_id,
            )

        # Do this last or else the entity registry update listener has been installed
        await super().async_internal_added_to_hass()