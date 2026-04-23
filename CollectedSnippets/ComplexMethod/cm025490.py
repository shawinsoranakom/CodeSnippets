async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new operation mode."""
        if operation_mode == STATE_PERFORMANCE:
            if self.is_away_mode_on:
                await self.async_turn_away_mode_off()
            await self.async_turn_boost_mode_on()
        elif operation_mode == STATE_ECO:
            if self.is_away_mode_on:
                await self.async_turn_away_mode_off()
            if self.is_boost_mode_on:
                await self.async_turn_boost_mode_off()
            await self.executor.async_execute_command(
                OverkizCommand.SET_DHW_MODE, OverkizCommandParam.AUTO_MODE
            )
        elif operation_mode == STATE_ELECTRIC:
            if self.is_away_mode_on:
                await self.async_turn_away_mode_off()
            if self.is_boost_mode_on:
                await self.async_turn_boost_mode_off()
            await self.executor.async_execute_command(
                OverkizCommand.SET_DHW_MODE, OverkizCommandParam.MANUAL_ECO_INACTIVE
            )
        elif operation_mode == STATE_OFF:
            await self.async_turn_away_mode_on()