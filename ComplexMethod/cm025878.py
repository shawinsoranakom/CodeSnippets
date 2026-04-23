async def options_updated(self, previous_config: DeconzConfig) -> None:
        """Manage entities affected by config entry options."""
        deconz_ids = []

        # Allow CLIP sensors

        if self.config.allow_clip_sensor != previous_config.allow_clip_sensor:
            if self.config.allow_clip_sensor:
                for add_device, device_id in self.clip_sensors:
                    add_device(EventType.ADDED, device_id)
            else:
                deconz_ids += [
                    sensor.deconz_id
                    for sensor in self.api.sensors.values()
                    if sensor.type.startswith("CLIP")
                ]

        # Allow Groups

        if self.config.allow_deconz_groups != previous_config.allow_deconz_groups:
            if self.config.allow_deconz_groups:
                for add_device, device_id in self.deconz_groups:
                    add_device(EventType.ADDED, device_id)
            else:
                deconz_ids += [group.deconz_id for group in self.api.groups.values()]

        # Allow adding new devices

        if self.config.allow_new_devices != previous_config.allow_new_devices:
            if self.config.allow_new_devices:
                self.load_ignored_devices()

        # Remove entities based on above categories

        entity_registry = er.async_get(self.hass)

        # Copy the ids since calling async_remove will modify the dict
        # and will cause a runtime error because the dict size changes
        # during iteration
        for entity_id, deconz_id in self.deconz_ids.copy().items():
            if deconz_id in deconz_ids and entity_registry.async_is_registered(
                entity_id
            ):
                # Removing an entity from the entity registry will also remove them
                # from Home Assistant
                entity_registry.async_remove(entity_id)