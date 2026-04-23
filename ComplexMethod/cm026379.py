async def async_turn_on(self) -> None:
        """Turn the entity on."""
        # Forward to self.turn_on if it's been overridden.
        if type(self).turn_on is not ClimateEntity.turn_on:
            await self.hass.async_add_executor_job(self.turn_on)
            return

        # If there are only two HVAC modes, and one of those modes is OFF,
        # then we can just turn on the other mode.
        if len(self.hvac_modes) == 2 and HVACMode.OFF in self.hvac_modes:
            for mode in self.hvac_modes:
                if mode != HVACMode.OFF:
                    await self.async_set_hvac_mode(mode)
                    return

        # Fake turn on
        for mode in (HVACMode.HEAT_COOL, HVACMode.HEAT, HVACMode.COOL):
            if mode not in self.hvac_modes:
                continue
            await self.async_set_hvac_mode(mode)
            return

        raise NotImplementedError