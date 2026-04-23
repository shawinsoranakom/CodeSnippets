def current_cover_tilt_position(self) -> int | None:
        """Return current position of cover tilt."""
        if self.is_vertical_tilt:
            char = self.service[CharacteristicsTypes.VERTICAL_TILT_CURRENT]
        elif self.is_horizontal_tilt:
            char = self.service[CharacteristicsTypes.HORIZONTAL_TILT_CURRENT]
        else:
            return None

        # Recalculate tilt_position. Convert arc to percent scale based on min/max values.
        tilt_position = char.value
        min_value = char.minValue
        max_value = char.maxValue
        total_range = int(max_value or 0) - int(min_value or 0)

        if (
            tilt_position is None
            or min_value is None
            or max_value is None
            or total_range <= 0
        ):
            return None

        # inverted scale
        if min_value == -90 and max_value == 0:
            return abs(int(100 / total_range * (tilt_position - max_value)))
        # normal scale
        return abs(int(100 / total_range * (tilt_position - min_value)))