def _get_state_from_coordinator_data(self) -> None:
        """Populate the entity fields with values from the coordinator data."""
        data = self.coordinator.data

        # Speed as a percentage
        if not data.power:
            self._attr_percentage = 0
        elif data.speed is None:
            self._attr_percentage = None
        elif data.speed is Speed.SuperSilent:
            self._attr_percentage = 1
        else:
            self._attr_percentage = ordered_list_item_to_percentage(
                SPEED_LIST, data.speed
            )

        # Preset mode
        if not data.power or data.mode is None:
            self._attr_preset_mode = None
        else:
            # Get key by value in dictionary
            self._attr_preset_mode = next(
                k for k, v in PRESET_MODES.items() if v == data.mode
            )