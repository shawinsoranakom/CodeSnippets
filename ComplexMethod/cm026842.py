def cleanup_removed_devices(self, data: FritzboxCoordinatorData) -> None:
        """Cleanup entity and device registry from removed devices."""
        available_ains = list(data.devices) + list(data.templates)
        entity_reg = er.async_get(self.hass)
        for entity in er.async_entries_for_config_entry(
            entity_reg, self.config_entry.entry_id
        ):
            if entity.unique_id.split("_")[0] not in available_ains:
                LOGGER.debug("Removing obsolete entity entry %s", entity.entity_id)
                entity_reg.async_remove(entity.entity_id)

        available_main_ains = [
            ain
            for ain, dev in (data.devices | data.templates | data.triggers).items()
            if dev.device_and_unit_id[1] is None
        ]
        device_reg = dr.async_get(self.hass)
        identifiers = {(DOMAIN, ain) for ain in available_main_ains}
        for device in dr.async_entries_for_config_entry(
            device_reg, self.config_entry.entry_id
        ):
            if not set(device.identifiers) & identifiers:
                LOGGER.debug("Removing obsolete device entry %s", device.name)
                device_reg.async_update_device(
                    device.id, remove_config_entry_id=self.config_entry.entry_id
                )