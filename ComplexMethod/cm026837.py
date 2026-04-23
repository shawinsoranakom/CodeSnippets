def async_update_battery(self, battery_level: Any, battery_charging: Any) -> None:
        """Update battery service if available.

        Only call this function if self._support_battery_level is True.
        """
        if not self._char_battery or not self._char_low_battery:
            # Battery appeared after homekit was started
            return

        battery_level = convert_to_float(battery_level)
        if battery_level is not None:
            if self._char_battery.value != battery_level:
                self._char_battery.set_value(battery_level)
            is_low_battery = 1 if battery_level < self.low_battery_threshold else 0
            if self._char_low_battery.value != is_low_battery:
                self._char_low_battery.set_value(is_low_battery)
                _LOGGER.debug(
                    "%s: Updated battery level to %d", self.entity_id, battery_level
                )

        # Charging state can appear after homekit was started
        if battery_charging is None or not self._char_charging:
            return

        hk_charging = HK_CHARGING if battery_charging else HK_NOT_CHARGING
        if self._char_charging.value != hk_charging:
            self._char_charging.set_value(hk_charging)
            _LOGGER.debug(
                "%s: Updated battery charging to %d", self.entity_id, hk_charging
            )