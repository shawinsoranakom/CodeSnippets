async def _global_control(
        self,
        main_operation: str | None = None,
        target_temperature: int | None = None,
        fan_mode: str | None = None,
        hvac_mode: str | None = None,
        swing_mode: str | None = None,
        leave_home: str | None = None,
    ) -> None:
        """Execute globalControl command with all parameters.

        There is no option to only set a single parameter, without passing
        all other values.
        """

        main_operation = self._control_backfill(
            main_operation, OverkizState.OVP_MAIN_OPERATION, OverkizCommandParam.ON
        )
        fan_mode = self._control_backfill(
            fan_mode,
            OverkizState.OVP_FAN_SPEED,
            OverkizCommandParam.AUTO,
        )
        # Sanitize fan mode: Overkiz is sometimes providing a state that
        # cannot be used as a command. Convert it to HA space and back to Overkiz
        if fan_mode not in FAN_MODES_TO_OVERKIZ.values():
            fan_mode = FAN_MODES_TO_OVERKIZ[OVERKIZ_TO_FAN_MODES[fan_mode]]

        hvac_mode = self._control_backfill(
            hvac_mode,
            OverkizState.OVP_MODE_CHANGE,
            OverkizCommandParam.AUTO,
        ).lower()  # Overkiz returns uppercase states that are not acceptable commands
        if hvac_mode.replace(" ", "") in [
            # Overkiz returns compound states like 'auto cooling' or 'autoHeating'
            # that are not valid commands and need to be mapped to 'auto'
            OverkizCommandParam.AUTOCOOLING,
            OverkizCommandParam.AUTOHEATING,
        ]:
            hvac_mode = OverkizCommandParam.AUTO

        swing_mode = self._control_backfill(
            swing_mode,
            OverkizState.OVP_SWING,
            OverkizCommandParam.STOP,
        )

        # AUTO_MANU parameter is not controlled by HA and is turned "off" when the device is on Holiday mode
        auto_manu_mode = self._control_backfill(
            None, OverkizState.CORE_AUTO_MANU_MODE, OverkizCommandParam.MANU
        )
        if self.preset_mode == PRESET_HOLIDAY_MODE:
            auto_manu_mode = OverkizCommandParam.OFF

        # In all the hvac modes except AUTO, the temperature command parameter is the target temperature
        temperature_command = None
        target_temperature = target_temperature or self.target_temperature
        if hvac_mode == OverkizCommandParam.AUTO:
            # In hvac mode AUTO, the temperature command parameter is a temperature_change
            # which is the delta between a pivot temperature (25) and the target temperature
            temperature_change = 0

            if target_temperature:
                temperature_change = target_temperature - AUTO_PIVOT_TEMPERATURE
            elif self.temperature_change:
                temperature_change = self.temperature_change

            # Keep temperature_change in the API accepted range
            temperature_change = min(
                max(temperature_change, AUTO_TEMPERATURE_CHANGE_MIN),
                AUTO_TEMPERATURE_CHANGE_MAX,
            )

            temperature_command = temperature_change
        else:
            # In other modes, the temperature command is the target temperature
            temperature_command = target_temperature

        command_data = [
            main_operation,  # Main Operation
            temperature_command,  # Temperature Command
            fan_mode,  # Fan Mode
            hvac_mode,  # Mode
            auto_manu_mode,  # Auto Manu Mode
        ]

        await self.executor.async_execute_command(
            OverkizCommand.GLOBAL_CONTROL, *command_data
        )