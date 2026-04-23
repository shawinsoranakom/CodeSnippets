def async_update_state(self, new_state: State) -> None:
        """Update light after state change."""
        # Handle State
        state = new_state.state
        attributes = new_state.attributes
        color_mode = attributes.get(ATTR_COLOR_MODE)
        self.char_on.set_value(int(state == STATE_ON))
        color_mode_changed = self._previous_color_mode != color_mode
        self._previous_color_mode = color_mode

        # Handle Brightness
        if (
            self.brightness_supported
            and (brightness := attributes.get(ATTR_BRIGHTNESS)) is not None
            and isinstance(brightness, (int, float))
        ):
            brightness = round(brightness / 255 * 100, 0)
            # The homeassistant component might report its brightness as 0 but is
            # not off. But 0 is a special value in homekit. When you turn on a
            # homekit accessory it will try to restore the last brightness state
            # which will be the last value saved by char_brightness.set_value.
            # But if it is set to 0, HomeKit will update the brightness to 100 as
            # it thinks 0 is off.
            #
            # Therefore, if the brightness is 0 and the device is still on,
            # the brightness is mapped to 1 otherwise the update is ignored in
            # order to avoid this incorrect behavior.
            if brightness == 0 and state == STATE_ON:
                brightness = 1
            self.char_brightness.set_value(brightness)
            if color_mode_changed:
                self.char_brightness.notify()

        # Handle Color - color must always be set before color temperature
        # or the iOS UI will not display it correctly.
        if self.color_supported:
            if color_temp := attributes.get(ATTR_COLOR_TEMP_KELVIN):
                hue, saturation = color_temperature_to_hs(color_temp)
            elif color_mode == ColorMode.WHITE:
                hue, saturation = 0, 0
            elif (
                (hue_sat := attributes.get(ATTR_HS_COLOR))
                and isinstance(hue_sat, (list, tuple))
                and len(hue_sat) == 2
            ):
                hue, saturation = hue_sat
            else:
                hue = None
                saturation = None
            if isinstance(hue, (int, float)) and isinstance(saturation, (int, float)):
                self.char_hue.set_value(round(hue, 0))
                self.char_saturation.set_value(round(saturation, 0))
                if color_mode_changed:
                    # If the color temp changed, be sure to force the color to update
                    self.char_hue.notify()
                    self.char_saturation.notify()

        # Handle white channels
        if CHAR_COLOR_TEMPERATURE in self.chars:
            color_temp = None
            if self.color_temp_supported:
                color_temp_kelvin = attributes.get(ATTR_COLOR_TEMP_KELVIN)
                if color_temp_kelvin is not None:
                    color_temp = color_temperature_kelvin_to_mired(color_temp_kelvin)
            elif color_mode == ColorMode.WHITE:
                color_temp = self.min_mireds
            if isinstance(color_temp, (int, float)):
                self.char_color_temp.set_value(round(color_temp, 0))
                if color_mode_changed:
                    self.char_color_temp.notify()