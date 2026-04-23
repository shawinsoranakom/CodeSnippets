def icon(self) -> str:
        """Return the sensor icon."""
        native_value = self.native_value
        if not self.available or native_value is None:
            return "mdi:battery-unknown"

        # This is similar to the logic in helpers.icon, but we have delegated the
        # decision about what mdi:battery-alert is to the device.
        icon = "mdi:battery"
        is_charging = self.is_charging
        if is_charging and native_value > 10:
            percentage = int(round(native_value / 20 - 0.01)) * 20
            icon += f"-charging-{percentage}"
        elif is_charging:
            icon += "-outline"
        elif self.is_low_battery:
            icon += "-alert"
        elif native_value < 95:
            percentage = max(int(round(native_value / 10 - 0.01)) * 10, 10)
            icon += f"-{percentage}"

        return icon