def icon(self) -> str | None:
        """Return the icon to use in the frontend."""
        if VentilationQuickmode.STANDBY in self._attributes[
            "vicare_quickmodes"
        ] and self._api.getVentilationQuickmode(VentilationQuickmode.STANDBY):
            return "mdi:fan-off"
        if hasattr(self, "_attr_preset_mode"):
            if self._attr_preset_mode == VentilationMode.VENTILATION:
                return "mdi:fan-clock"
            if self._attr_preset_mode in [
                VentilationMode.SENSOR_DRIVEN,
                VentilationMode.SENSOR_OVERRIDE,
            ]:
                return "mdi:fan-auto"
            if self._attr_preset_mode == VentilationMode.PERMANENT:
                if self._attr_percentage == 0:
                    return "mdi:fan-off"
                if self._attr_percentage is not None:
                    level = 1 + ORDERED_NAMED_FAN_SPEEDS.index(
                        percentage_to_ordered_list_item(
                            ORDERED_NAMED_FAN_SPEEDS, self._attr_percentage
                        )
                    )
                    if level < 4:  # fan-speed- only supports 1-3
                        return f"mdi:fan-speed-{level}"
        return "mdi:fan"