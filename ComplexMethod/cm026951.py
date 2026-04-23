def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255.

        Z-Wave multilevel switches use a range of [0, 99] to control brightness.
        """
        if self.info.primary_value.value is None:
            return None
        if self._target_brightness and self.info.primary_value.value is False:
            # Binary switch exists and is turned off
            return 0

        # Brightness is encoded in the color channels by scaling them lower than 255
        color_values = [
            v.value
            for v in self._get_color_values()
            if v is not None and v.value is not None
        ]
        return max(color_values) if color_values else 0