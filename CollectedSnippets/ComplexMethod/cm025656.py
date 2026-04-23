async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode (off, heat, cool, heat_cool, or auto/schedule)."""
        if hvac_mode == self.hvac_mode:
            return

        api = self.coordinator.api
        current_schedule = self.device.get("select_schedule")

        # OFF: single API call
        if hvac_mode == HVACMode.OFF:
            await api.set_regulation_mode(hvac_mode.value)
            return

        # Manual mode (heat/cool/heat_cool) without a schedule: set regulation only
        if (
            current_schedule is None
            and hvac_mode != HVACMode.AUTO
            and (
                regulation := self._regulation_mode_for_hvac(hvac_mode)
                or self._previous_action_mode
            )
        ):
            await api.set_regulation_mode(regulation)
            return

        # Manual mode: ensure regulation and turn off schedule when needed
        if hvac_mode in (HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL):
            regulation = self._regulation_mode_for_hvac(hvac_mode) or (
                self._previous_action_mode
                if self.hvac_mode in (HVACMode.HEAT_COOL, HVACMode.OFF)
                else None
            )
            if regulation:
                await api.set_regulation_mode(regulation)

            if (
                self.hvac_mode == HVACMode.OFF and current_schedule not in (None, "off")
            ) or (self.hvac_mode == HVACMode.AUTO and current_schedule is not None):
                await api.set_schedule_state(
                    self._location, STATE_OFF, current_schedule
                )
            return

        # AUTO: restore schedule and regulation
        desired_schedule = current_schedule
        if desired_schedule and desired_schedule != "off":
            self._last_active_schedule = desired_schedule
        elif desired_schedule == "off":
            desired_schedule = self._last_active_schedule

        if not desired_schedule:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key=ERROR_NO_SCHEDULE,
            )

        if self._previous_action_mode:
            if self.hvac_mode == HVACMode.OFF:
                await api.set_regulation_mode(self._previous_action_mode)
            await api.set_schedule_state(self._location, STATE_ON, desired_schedule)