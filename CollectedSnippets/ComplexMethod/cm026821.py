def async_update_state(self, new_state: State) -> None:
        """Update fan after state change."""
        # Handle State
        state = new_state.state
        attributes = new_state.attributes
        if state in (STATE_ON, STATE_OFF):
            self._state = 1 if state == STATE_ON else 0
            self.char_active.set_value(self._state)

        # Handle Direction
        if self.char_direction is not None:
            direction = new_state.attributes.get(ATTR_DIRECTION)
            if direction in (DIRECTION_FORWARD, DIRECTION_REVERSE):
                hk_direction = 1 if direction == DIRECTION_REVERSE else 0
                self.char_direction.set_value(hk_direction)

        # Handle Speed
        if self.char_speed is not None and state != STATE_OFF:
            # We do not change the homekit speed when turning off
            # as it will clear the restore state
            percentage = attributes.get(ATTR_PERCENTAGE)
            # If the homeassistant component reports its speed as the first entry
            # in its speed list but is not off, the hk_speed_value is 0. But 0
            # is a special value in homekit. When you turn on a homekit accessory
            # it will try to restore the last rotation speed state which will be
            # the last value saved by char_speed.set_value. But if it is set to
            # 0, HomeKit will update the rotation speed to 100 as it thinks 0 is
            # off.
            #
            # Therefore, if the hk_speed_value is 0 and the device is still on,
            # the rotation speed is mapped to 1 otherwise the update is ignored
            # in order to avoid this incorrect behavior.
            if percentage == 0 and state == STATE_ON:
                percentage = max(1, self.char_speed.properties[PROP_MIN_STEP])
            if percentage is not None:
                self.char_speed.set_value(percentage)

        # Handle Oscillating
        if self.char_swing is not None:
            oscillating = attributes.get(ATTR_OSCILLATING)
            if isinstance(oscillating, bool):
                hk_oscillating = 1 if oscillating else 0
                self.char_swing.set_value(hk_oscillating)

        current_preset_mode = attributes.get(ATTR_PRESET_MODE)
        if self.char_target_fan_state is not None:
            # Handle single preset mode
            self.char_target_fan_state.set_value(int(current_preset_mode is not None))
            return

        # Handle multiple preset modes
        for preset_mode, char in self.preset_mode_chars.items():
            hk_value = 1 if preset_mode == current_preset_mode else 0
            char.set_value(hk_value)