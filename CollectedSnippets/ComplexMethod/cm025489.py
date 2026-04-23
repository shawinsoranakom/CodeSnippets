async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""

        if operation_mode == STATE_PERFORMANCE:
            if self.executor.has_command(OverkizCommand.SET_BOOST_MODE):
                await self.executor.async_execute_command(
                    OverkizCommand.SET_BOOST_MODE, OverkizCommand.ON
                )

            if self.executor.has_command(OverkizCommand.SET_BOOST_MODE_DURATION):
                await self.executor.async_execute_command(
                    OverkizCommand.SET_BOOST_MODE_DURATION, 7
                )
                await self.executor.async_execute_command(
                    OverkizCommand.REFRESH_BOOST_MODE_DURATION
                )

            if self.executor.has_command(OverkizCommand.SET_CURRENT_OPERATING_MODE):
                current_operating_mode = self.executor.select_state(
                    OverkizState.CORE_OPERATING_MODE
                )

                if current_operating_mode and isinstance(current_operating_mode, dict):
                    await self.executor.async_execute_command(
                        OverkizCommand.SET_CURRENT_OPERATING_MODE,
                        {
                            OverkizCommandParam.RELAUNCH: OverkizCommandParam.ON,
                            OverkizCommandParam.ABSENCE: OverkizCommandParam.OFF,
                        },
                    )

            return

        if self._is_boost_mode_on:
            # We're setting a non Boost mode and the device is currently in Boost mode
            # The following code removes all boost operations
            if self.executor.has_command(OverkizCommand.SET_BOOST_MODE):
                await self.executor.async_execute_command(
                    OverkizCommand.SET_BOOST_MODE, OverkizCommand.OFF
                )

            if self.executor.has_command(OverkizCommand.SET_CURRENT_OPERATING_MODE):
                current_operating_mode = self.executor.select_state(
                    OverkizState.CORE_OPERATING_MODE
                )

                if current_operating_mode and isinstance(current_operating_mode, dict):
                    await self.executor.async_execute_command(
                        OverkizCommand.SET_CURRENT_OPERATING_MODE,
                        {
                            OverkizCommandParam.RELAUNCH: OverkizCommandParam.OFF,
                            OverkizCommandParam.ABSENCE: OverkizCommandParam.OFF,
                        },
                    )

        await self.executor.async_execute_command(
            OverkizCommand.SET_DHW_MODE, self.operation_mode_to_overkiz[operation_mode]
        )

        if self.executor.has_command(OverkizCommand.REFRESH_BOOST_MODE_DURATION):
            await self.executor.async_execute_command(
                OverkizCommand.REFRESH_BOOST_MODE_DURATION
            )

        if self.executor.has_command(OverkizCommand.REFRESH_DHW_MODE):
            await self.executor.async_execute_command(OverkizCommand.REFRESH_DHW_MODE)