def state_updated(self, state: bool, **kwargs: Any) -> None:
        """Handle state updates."""
        self._on_off_state = state
        if attributes := kwargs.get("attributes"):
            if "brightness" in attributes:
                brightness = float(attributes["brightness"])
                percent_bright = brightness / TASMOTA_BRIGHTNESS_MAX
                self._attr_brightness = round(percent_bright * 255)
            if "color_hs" in attributes:
                self._attr_hs_color = attributes["color_hs"]
            if "color_temp" in attributes:
                self._color_temp = attributes["color_temp"]
            if "effect" in attributes:
                self._attr_effect = attributes["effect"]
            if "white_value" in attributes:
                white_value = float(attributes["white_value"])
                percent_white = white_value / TASMOTA_BRIGHTNESS_MAX
                self._white_value = round(percent_white * 255)
            if self._tasmota_entity.light_type == LIGHT_TYPE_RGBW:
                # Tasmota does not support RGBW mode, set mode to white or hs
                if self._white_value == 0:
                    self._attr_color_mode = ColorMode.HS
                else:
                    self._attr_color_mode = ColorMode.WHITE
            elif self._tasmota_entity.light_type == LIGHT_TYPE_RGBCW:
                # Tasmota does not support RGBWW mode, set mode to ct or hs
                if self._white_value == 0:
                    self._attr_color_mode = ColorMode.HS
                else:
                    self._attr_color_mode = ColorMode.COLOR_TEMP

        self.async_write_ha_state()