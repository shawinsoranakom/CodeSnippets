def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device = next(
            (
                device
                for device in self.coordinator.data
                if device["uid"] == self._attr_unique_id
            ),
            None,
        )
        if device is not None and "state" in device:
            state = device["state"]
            if "currentTemperature" in state:
                self._attr_current_temperature = state["currentTemperature"]
            if "targetTemperature" in state:
                self._attr_target_temperature = state["targetTemperature"]
            if "heatingCoolingState" in state:
                self._attr_hvac_mode = HVAC_MAP[state["heatingCoolingState"]]
        super()._handle_coordinator_update()