def _async_update_fan_state(self, new_state: State) -> None:
        """Update state without rechecking the device features."""
        attributes = new_state.attributes

        if CHAR_SWING_MODE in self.fan_chars and (
            swing_mode := attributes.get(ATTR_SWING_MODE)
        ):
            swing = 1 if swing_mode in PRE_DEFINED_SWING_MODES else 0
            self.char_swing.set_value(swing)

        fan_mode = attributes.get(ATTR_FAN_MODE)
        fan_mode_lower = fan_mode.lower() if isinstance(fan_mode, str) else None
        if (
            CHAR_ROTATION_SPEED in self.fan_chars
            and fan_mode_lower in self.ordered_fan_speeds
        ):
            self.char_speed.set_value(
                ordered_list_item_to_percentage(self.ordered_fan_speeds, fan_mode_lower)
            )

        if CHAR_TARGET_FAN_STATE in self.fan_chars:
            self.char_target_fan_state.set_value(1 if fan_mode_lower == FAN_AUTO else 0)

        if CHAR_CURRENT_FAN_STATE in self.fan_chars and (
            hvac_action := attributes.get(ATTR_HVAC_ACTION)
        ):
            self.char_current_fan_state.set_value(
                HC_HASS_TO_HOMEKIT_FAN_STATE[hvac_action]
            )

        self.char_active.set_value(
            int(new_state.state != HVACMode.OFF and fan_mode_lower != FAN_OFF)
        )