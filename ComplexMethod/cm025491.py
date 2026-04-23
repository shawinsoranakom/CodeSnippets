async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new operation mode."""

        if operation_mode == STATE_ECO:
            if self.is_boost_mode_on:
                await self.async_turn_boost_mode_off(refresh_afterwards=False)

            if self.is_away_mode_on:
                await self.async_turn_away_mode_off(refresh_afterwards=False)

            await self.executor.async_execute_command(
                OverkizCommand.SET_DHW_MODE,
                OverkizCommandParam.MANUAL_ECO_ACTIVE,
                refresh_afterwards=False,
            )
            # ECO changes the target temperature so we have to refresh it
            await self.executor.async_execute_command(
                OverkizCommand.REFRESH_TARGET_TEMPERATURE, refresh_afterwards=False
            )
            await self.coordinator.async_refresh()

        elif operation_mode == STATE_PERFORMANCE:
            if self.is_boost_mode_on:
                await self.async_turn_boost_mode_off(refresh_afterwards=False)
            if self.is_away_mode_on:
                await self.async_turn_away_mode_off(refresh_afterwards=False)

            await self.executor.async_execute_command(
                OverkizCommand.SET_DHW_MODE,
                OverkizCommandParam.AUTO_MODE,
                refresh_afterwards=False,
            )

            await self.coordinator.async_refresh()

        elif operation_mode == STATE_HEAT_PUMP:
            refresh_target_temp = False
            if self.is_state_performance:
                # Switching from STATE_PERFORMANCE to STATE_HEAT_PUMP
                #  changes the target temperature and requires a target temperature refresh
                refresh_target_temp = True

            if self.is_boost_mode_on:
                await self.async_turn_boost_mode_off(refresh_afterwards=False)
            if self.is_away_mode_on:
                await self.async_turn_away_mode_off(refresh_afterwards=False)

            await self.executor.async_execute_command(
                OverkizCommand.SET_DHW_MODE,
                OverkizCommandParam.MANUAL_ECO_INACTIVE,
                refresh_afterwards=False,
            )

            if refresh_target_temp:
                await self.executor.async_execute_command(
                    OverkizCommand.REFRESH_TARGET_TEMPERATURE,
                    refresh_afterwards=False,
                )

            await self.coordinator.async_refresh()

        elif operation_mode == STATE_ELECTRIC:
            if self.is_away_mode_on:
                await self.async_turn_away_mode_off(refresh_afterwards=False)
            if not self.is_boost_mode_on:
                await self.async_turn_boost_mode_on(refresh_afterwards=False)
            await self.coordinator.async_refresh()