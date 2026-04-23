async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the device.

        If percentage is 0, turn off the fan. Otherwise, ensure the fan is on,
        set manual mode if needed, and set the speed.
        """
        if percentage == 0:
            # Turning off is a special case: do not set speed or mode
            if not await self.device.turn_off():
                if self.device.last_response:
                    raise HomeAssistantError(
                        "An error occurred while turning off: "
                        + self.device.last_response.message
                    )
                raise HomeAssistantError("Failed to turn off fan, no response found.")
            self.async_write_ha_state()
            return

        # If the fan is off, turn it on first
        if not self.device.is_on:
            if not await self.device.turn_on():
                if self.device.last_response:
                    raise HomeAssistantError(
                        "An error occurred while turning on: "
                        + self.device.last_response.message
                    )
                raise HomeAssistantError("Failed to turn on fan, no response found.")

        # Switch to manual mode if not already set
        if self.device.state.mode not in (VS_FAN_MODE_MANUAL, VS_FAN_MODE_NORMAL):
            if not await self.device.set_manual_mode():
                if self.device.last_response:
                    raise HomeAssistantError(
                        "An error occurred while setting manual mode."
                        + self.device.last_response.message
                    )
                raise HomeAssistantError(
                    "Failed to set manual mode, no response found."
                )

        # Calculate the speed level and set it
        if not await self.device.set_fan_speed(
            percentage_to_ordered_list_item(self.device.fan_levels, percentage)
        ):
            if self.device.last_response:
                raise HomeAssistantError(
                    "An error occurred while changing fan speed: "
                    + self.device.last_response.message
                )
            raise HomeAssistantError("Failed to set fan speed, no response found.")

        self.async_write_ha_state()