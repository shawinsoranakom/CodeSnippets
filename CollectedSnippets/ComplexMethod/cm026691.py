def _async_add_remove_devices(self) -> None:
        """Add new devices, remove non-existing devices."""
        if not self._plants_last_update:
            self._plants_last_update = set(self.fyta.plant_list.keys())

        if (
            current_plants := set(self.fyta.plant_list.keys())
        ) == self._plants_last_update:
            return

        _LOGGER.debug(
            "Check for new and removed plant(s): old plants: %s; new plants: %s",
            ", ".join(map(str, self._plants_last_update)),
            ", ".join(map(str, current_plants)),
        )

        # remove old plants
        if removed_plants := self._plants_last_update - current_plants:
            _LOGGER.debug("Removed plant(s): %s", ", ".join(map(str, removed_plants)))

            device_registry = dr.async_get(self.hass)
            for plant_id in removed_plants:
                if device := device_registry.async_get_device(
                    identifiers={
                        (
                            DOMAIN,
                            f"{self.config_entry.entry_id}-{plant_id}",
                        )
                    }
                ):
                    device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self.config_entry.entry_id,
                    )
                    _LOGGER.debug("Device removed from device registry: %s", device.id)

        # add new devices
        if new_plants := current_plants - self._plants_last_update:
            _LOGGER.debug("New plant(s) found: %s", ", ".join(map(str, new_plants)))
            for plant_id in new_plants:
                for callback in self.new_device_callbacks:
                    callback(plant_id)
                    _LOGGER.debug("Device added: %s", plant_id)

        self._plants_last_update = current_plants