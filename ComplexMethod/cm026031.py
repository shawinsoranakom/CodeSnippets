def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        old_brightness = self._attr_brightness
        if old_brightness == 0:
            # Dim down from max if applicable, also avoids a "dim" command if an "on" is more appropriate
            old_brightness = 255
        self._attr_brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        brightness_diff = self.normalize_x10_brightness(
            self._attr_brightness
        ) - self.normalize_x10_brightness(old_brightness)
        command_suffix = ""
        # heyu has quite a messy command structure - we'll just deal with it here
        if brightness_diff == 0:
            if self._is_cm11a:
                command_prefix = "on"
            else:
                command_prefix = "fon"
        elif brightness_diff > 0:
            if self._is_cm11a:
                command_prefix = "bright"
            else:
                command_prefix = "fbright"
            command_suffix = f" {brightness_diff}"
        else:
            if self._is_cm11a:
                if self._attr_is_on:
                    command_prefix = "dim"
                else:
                    command_prefix = "dimb"
            else:
                command_prefix = "fdim"
            command_suffix = f" {-brightness_diff}"
        x10_command(f"{command_prefix} {self._id}{command_suffix}")
        self._attr_is_on = True