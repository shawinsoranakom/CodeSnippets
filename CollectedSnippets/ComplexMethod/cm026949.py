def _calculate_color_support(self) -> None:
        """Calculate light colors."""
        (red, green, blue, warm_white, cool_white) = self._get_color_values()
        # RGB support
        if red and green and blue:
            self._supports_color = True
        # color temperature support
        if warm_white and cool_white:
            self._supports_color_temp = True
        # only one white channel (warm white or cool white) = rgbw support
        elif (red and green and blue and warm_white) or cool_white:
            self._supports_rgbw = True