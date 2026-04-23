def async_update_battery(
        self,
        battery_percentage: int | None,
        is_charging: bool | None,
        is_wired: bool | None,
    ) -> None:
        """Update the battery sensor value and icon."""
        self._attr_native_value = battery_percentage
        if battery_percentage is None:
            # Battery percentage is unknown
            self._attr_icon = "mdi:battery-unknown"
        elif is_wired:
            # Motor is wired and does not have a battery
            self._attr_icon = "mdi:power-plug-outline"
        elif battery_percentage > 90 and not is_charging:
            # Full battery icon if battery > 90% and not charging
            self._attr_icon = "mdi:battery"
        elif battery_percentage <= 5 and not is_charging:
            # Empty battery icon with alert if battery <= 5% and not charging
            self._attr_icon = "mdi:battery-alert-variant-outline"
        else:
            battery_icon_prefix = (
                "mdi:battery-charging" if is_charging else "mdi:battery"
            )
            battery_percentage_multiple_ten = ceil(battery_percentage / 10) * 10
            self._attr_icon = f"{battery_icon_prefix}-{battery_percentage_multiple_ten}"
        self.async_write_ha_state()