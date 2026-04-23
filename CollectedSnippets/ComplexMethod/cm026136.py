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
            if "on" in state:
                self._attr_is_on = state["on"]
            if "brightness" in state:
                self._attr_brightness = round(state["brightness"] / 100 * 255)
            if "hue" in state and "saturation" in state:
                self._attr_hs_color = (state["hue"], state["saturation"])
        super()._handle_coordinator_update()