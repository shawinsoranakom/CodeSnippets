def set_chars(self, char_values: dict[str, Any]) -> None:
        """Set characteristic values."""
        _LOGGER.debug("Fan set_chars: %s", char_values)
        if CHAR_ACTIVE in char_values:
            if char_values[CHAR_ACTIVE]:
                # If the device supports set speed we
                # do not want to turn on as it will take
                # the fan to 100% than to the desired speed.
                #
                # Setting the speed will take care of turning
                # on the fan if FanEntityFeature.SET_SPEED is set.
                if not self.char_speed or CHAR_ROTATION_SPEED not in char_values:
                    self.set_state(1)
            else:
                # Its off, nothing more to do as setting the
                # other chars will likely turn it back on which
                # is what we want to avoid
                self.set_state(0)
                return

        if CHAR_SWING_MODE in char_values:
            self.set_oscillating(char_values[CHAR_SWING_MODE])
        if CHAR_ROTATION_DIRECTION in char_values:
            self.set_direction(char_values[CHAR_ROTATION_DIRECTION])

        # We always do this LAST to ensure they
        # get the speed they asked for
        if CHAR_ROTATION_SPEED in char_values:
            self.set_percentage(char_values[CHAR_ROTATION_SPEED])
        if CHAR_TARGET_FAN_STATE in char_values:
            self.set_single_preset_mode(char_values[CHAR_TARGET_FAN_STATE])