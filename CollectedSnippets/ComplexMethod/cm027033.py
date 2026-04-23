def update(self) -> None:
        """Update the state."""
        super().update()

        # Dimmable and RGB lights can be on based on different
        # properties, so we need to check here several values
        # to see if the light is on.
        light_is_on = self.current_binary_state
        with suppress(TypeError):
            if self.fibaro_device.brightness != 0:
                light_is_on = True
        with suppress(TypeError):
            if self.fibaro_device.current_program != 0:
                light_is_on = True
        with suppress(TypeError):
            if self.fibaro_device.current_program_id != 0:
                light_is_on = True
        self._attr_is_on = light_is_on

        # Brightness handling
        if brightness_supported(self.supported_color_modes):
            self._attr_brightness = scaleto255(self.fibaro_device.value.int_value())

        # Color handling
        if (
            color_supported(self.supported_color_modes)
            and self.fibaro_device.color.has_color
        ):
            # Fibaro communicates the color as an 'R, G, B, W' string
            rgbw = self.fibaro_device.color.rgbw_color
            if rgbw == (0, 0, 0, 0) and self.fibaro_device.last_color_set.has_color:
                rgbw = self.fibaro_device.last_color_set.rgbw_color

            if self.color_mode == ColorMode.RGB:
                self._attr_rgb_color = rgbw[:3]
            else:
                self._attr_rgbw_color = rgbw