async def _operate(
        self,
        power: str | None = None,
        mode: str | None = None,
        fan: str | None = None,
        target_temperature: int | None = None,
    ) -> None:
        """Send request to central unit."""

        if power is None:
            power = ApiStateCommand.ON
            if self.hvac_mode == HVACMode.OFF:
                power = ApiStateCommand.OFF
        if mode is None:
            mode = HVAC_MODE_HASS_TO_SB[self.hvac_mode]
        if fan is None:
            fan = FAN_HASS_TO_SB[self.fan_mode]
        if target_temperature is None:
            target_temperature = int(self.target_temperature or 0)

        state: dict[str, int | str] = {
            ApiAttribute.POWER: power,
            ApiAttribute.MODE: mode,
            ApiAttribute.FAN: fan,
            ApiAttribute.CONFIGURED_TEMPERATURE: target_temperature,
        }

        try:
            await self.coordinator.api.set_state(self._device.id, state)
        except (SwitchBeeError, SwitchBeeDeviceOfflineError) as exp:
            raise HomeAssistantError(
                f"Failed to set {self.name} state {state}, error: {exp!s}"
            ) from exp

        await self.coordinator.async_refresh()