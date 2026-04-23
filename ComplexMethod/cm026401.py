def _add_remove_zones(self) -> None:
        """Add newly discovered zones and remove nonexistent ones."""
        if self.data is None:
            # Likely a setup error; ignore.
            # Despite what mypy thinks, this is still reachable. Without this check,
            # the test_connect_retry test in test_init.py fails.
            return  # type: ignore[unreachable]

        device_registry = dr.async_get(self.hass)
        devices = dr.async_entries_for_config_entry(
            device_registry, self.config_entry.entry_id
        )
        previous_zones: set[str] = set()
        previous_zones_by_id: dict[str, DeviceEntry] = {}
        previous_controllers: set[str] = set()
        previous_controllers_by_id: dict[str, DeviceEntry] = {}
        for device in devices:
            for domain, identifier in device.identifiers:
                if domain == DOMAIN:
                    if device.model == MODEL_ZONE:
                        previous_zones.add(identifier)
                        previous_zones_by_id[identifier] = device
                    else:
                        previous_controllers.add(identifier)
                        previous_controllers_by_id[identifier] = device
                    continue

        current_zones = {str(zone_id) for zone_id in self.data.zones}
        current_controllers = {
            str(controller_id) for controller_id in self.data.controllers
        }

        if removed_zones := previous_zones - current_zones:
            LOGGER.debug("Removed zones: %s", ", ".join(removed_zones))
            for zone_id in removed_zones:
                device_registry.async_update_device(
                    device_id=previous_zones_by_id[zone_id].id,
                    remove_config_entry_id=self.config_entry.entry_id,
                )

        if removed_controllers := previous_controllers - current_controllers:
            LOGGER.debug("Removed controllers: %s", ", ".join(removed_controllers))
            for controller_id in removed_controllers:
                device_registry.async_update_device(
                    device_id=previous_controllers_by_id[controller_id].id,
                    remove_config_entry_id=self.config_entry.entry_id,
                )

        if new_controller_ids := current_controllers - previous_controllers:
            LOGGER.debug("New controllers found: %s", ", ".join(new_controller_ids))
            new_controllers = [
                self.data.controllers[controller_id]
                for controller_id in map(int, new_controller_ids)
            ]
            for new_controller_callback in self.new_controllers_callbacks:
                new_controller_callback(new_controllers)

        if new_zone_ids := current_zones - previous_zones:
            LOGGER.debug("New zones found: %s", ", ".join(new_zone_ids))
            new_zones = [
                (
                    self.data.zones[zone_id],
                    self.data.zone_id_to_controller[zone_id],
                )
                for zone_id in map(int, new_zone_ids)
            ]
            for new_zone_callback in self.new_zones_callbacks:
                new_zone_callback(new_zones)