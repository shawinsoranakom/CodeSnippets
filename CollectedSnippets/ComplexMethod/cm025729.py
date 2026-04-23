async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""

        if preset_mode is None:
            preset_mode = self._preset_mode

        if percentage is None:
            percentage = self._default_on_speed

        new_speed = percentage_to_ordered_list_item(
            ORDERED_NAMED_FAN_SPEEDS, percentage
        )

        async with self.coordinator.async_connect_and_update() as device:
            if preset_mode != self._preset_mode:
                if command := PRESET_TO_COMMAND.get(preset_mode):
                    await device.send_command(command)
                else:
                    raise UnsupportedPreset(f"The preset {preset_mode} is unsupported")

            if preset_mode == PRESET_MODE_NORMAL:
                await device.send_fan_speed(int(new_speed))
            elif preset_mode == PRESET_MODE_AFTER_COOKING_MANUAL:
                await device.send_after_cooking(int(new_speed))
            elif preset_mode == PRESET_MODE_AFTER_COOKING_AUTO:
                await device.send_after_cooking(0)