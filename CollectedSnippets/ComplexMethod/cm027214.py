def _initialize_fan_speeds(self) -> None:
        """Initialize fan speeds."""
        azd_speeds: dict[int, int] = self.get_airzone_value(AZD_SPEEDS)
        max_speed = max(azd_speeds)

        fan_speeds: dict[int, str]
        if speeds_map := FAN_SPEED_MAPS.get(max_speed):
            fan_speeds = speeds_map
        else:
            fan_speeds = {}

            for speed in azd_speeds:
                if speed != 0:
                    fan_speeds[speed] = f"{int(round((speed * 100) / max_speed, 0))}%"

        if 0 in azd_speeds:
            fan_speeds = FAN_SPEED_AUTO | fan_speeds

        self._speeds = {}
        for key, value in fan_speeds.items():
            _key = azd_speeds.get(key)
            if _key is not None:
                self._speeds[_key] = value

        self._speeds_reverse = {v: k for k, v in self._speeds.items()}
        self._attr_fan_modes = list(self._speeds_reverse)

        self._attr_supported_features |= ClimateEntityFeature.FAN_MODE