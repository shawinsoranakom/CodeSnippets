def async_update_state_callback(self, new_state: State | None) -> None:
        """Handle state change listener callback."""
        _LOGGER.debug("New_state: %s", new_state)
        # HomeKit handles unavailable state via the available property
        # so we should not propagate it here
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        battery_state = None
        battery_charging_state = None
        if (
            not self.linked_battery_sensor
            and ATTR_BATTERY_LEVEL in new_state.attributes
        ):
            battery_state = new_state.attributes.get(ATTR_BATTERY_LEVEL)
        if (
            not self.linked_battery_charging_sensor
            and ATTR_BATTERY_CHARGING in new_state.attributes
        ):
            battery_charging_state = new_state.attributes.get(ATTR_BATTERY_CHARGING)
        if battery_state is not None or battery_charging_state is not None:
            self.async_update_battery(battery_state, battery_charging_state)
        self.async_update_state(new_state)