async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        # Set name based on source sensor(s)
        if self._source_sensors:
            entity_reg = er.async_get(self.hass)
            device_id = None
            source_name = None
            # Check first sensor
            if source_entry := entity_reg.async_get(self._source_sensors[0]):
                device_id = source_entry.device_id
                # For combined mode, always use Watts because we may have different source units; for inverted mode, copy source unit
                if self._is_combined:
                    self._attr_native_unit_of_measurement = UnitOfPower.WATT
                else:
                    self._attr_native_unit_of_measurement = (
                        source_entry.unit_of_measurement
                    )
                # Get source name from registry
                source_name = source_entry.name or source_entry.original_name
            # Assign power sensor to same device as source sensor(s)
            # Note: We use manual entity registry update instead of _attr_device_info
            # because device assignment depends on runtime information from the entity
            # registry (which source sensor has a device). This information isn't
            # available during __init__, and the entity is already registered before
            # async_added_to_hass runs, making the standard _attr_device_info pattern
            # incompatible with this use case.
            # If first sensor has no device and we have a second sensor, check it
            if not device_id and len(self._source_sensors) > 1:
                if source_entry := entity_reg.async_get(self._source_sensors[1]):
                    device_id = source_entry.device_id
            # Update entity registry entry with device_id
            if device_id and (power_entry := entity_reg.async_get(self.entity_id)):
                entity_reg.async_update_entity(
                    power_entry.entity_id, device_id=device_id
                )
            else:
                self._attr_has_entity_name = False

            # Set name for inverted mode
            if self._is_inverted:
                if source_name:
                    self._attr_name = f"{source_name} Inverted"
                else:
                    # Fall back to entity_id if no name in registry
                    sensor_name = split_entity_id(self._source_sensors[0])[1].replace(
                        "_", " "
                    )
                    self._attr_name = f"{sensor_name.title()} Inverted"

        # Set name for combined mode
        if self._is_combined:
            self._attr_name = f"{self._source_type.title()} Power"

        self._update_state()

        # Track state changes on all source sensors
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self._source_sensors,
                self._async_state_changed_listener,
            )
        )
        _set_result_unless_done(self.add_finished)