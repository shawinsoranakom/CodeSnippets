def run(self) -> None:
        """Handle accessory driver started event."""
        if state := self.hass.states.get(self.entity_id):
            self.async_update_state_callback(state)
        self._update_available_from_state(state)
        self._subscriptions.append(
            async_track_state_change_event(
                self.hass,
                [self.entity_id],
                self.async_update_event_state_callback,
                job_type=HassJobType.Callback,
            )
        )

        battery_charging_state = None
        battery_state = None
        if self.linked_battery_sensor and (
            linked_battery_sensor_state := self.hass.states.get(
                self.linked_battery_sensor
            )
        ):
            battery_state = linked_battery_sensor_state.state
            battery_charging_state = linked_battery_sensor_state.attributes.get(
                ATTR_BATTERY_CHARGING
            )
            self._subscriptions.append(
                async_track_state_change_event(
                    self.hass,
                    [self.linked_battery_sensor],
                    self.async_update_linked_battery_callback,
                    job_type=HassJobType.Callback,
                )
            )
        elif state is not None:
            battery_state = state.attributes.get(ATTR_BATTERY_LEVEL)
        if self.linked_battery_charging_sensor:
            state = self.hass.states.get(self.linked_battery_charging_sensor)
            battery_charging_state = state and state.state == STATE_ON
            self._subscriptions.append(
                async_track_state_change_event(
                    self.hass,
                    [self.linked_battery_charging_sensor],
                    self.async_update_linked_battery_charging_callback,
                    job_type=HassJobType.Callback,
                )
            )
        elif battery_charging_state is None and state is not None:
            battery_charging_state = state.attributes.get(ATTR_BATTERY_CHARGING)

        if battery_state is not None or battery_charging_state is not None:
            self.async_update_battery(battery_state, battery_charging_state)