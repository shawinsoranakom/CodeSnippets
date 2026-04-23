async def _async_control_heating(
        self, _time: datetime | None = None, force: bool = False
    ) -> None:
        """Check if we need to turn heating on or off."""
        called_by_timer = _time is not None

        async with self._temp_lock:
            if not self._active and None not in (
                self._cur_temp,
                self._target_temp,
            ):
                self._active = True
                _LOGGER.debug(
                    (
                        "Obtained current and target temperature. "
                        "Generic thermostat active. %s, %s"
                    ),
                    self._cur_temp,
                    self._target_temp,
                )

            if not self._active or self._hvac_mode == HVACMode.OFF:
                return

            if force and called_by_timer and self.max_cycle_duration:
                # We were invoked due to `max_cycle_duration`, so turn off
                _LOGGER.debug(
                    "Turning off heater %s due to max cycle time of %s",
                    self.heater_entity_id,
                    self.max_cycle_duration,
                )
                self._cancel_cycle_timer()
                await self._async_heater_turn_off()
                return

            assert self._cur_temp is not None and self._target_temp is not None
            too_cold = self._target_temp > self._cur_temp + self._cold_tolerance
            too_hot = self._target_temp < self._cur_temp - self._hot_tolerance
            now = dt_util.utcnow()

            if self._is_device_active:
                if (self.ac_mode and too_cold) or (not self.ac_mode and too_hot):
                    # Make sure it's past the `min_cycle_duration` before turning off
                    if (
                        self._last_toggled_time + self.min_cycle_duration <= now
                        or force
                    ):
                        _LOGGER.debug("Turning off heater %s", self.heater_entity_id)
                        await self._async_heater_turn_off()
                    elif self._check_callback is None:
                        _LOGGER.debug(
                            "Minimum cycle time not reached, check again at %s",
                            self._last_toggled_time + self.min_cycle_duration,
                        )
                        self._check_callback = async_call_later(
                            self.hass,
                            now - self._last_toggled_time + self.min_cycle_duration,
                            self._async_timer_control_heating,
                        )
                elif called_by_timer:
                    # This is a keep-alive call, so ensure it's on
                    _LOGGER.debug(
                        "Keep-alive - Turning on heater %s",
                        self.heater_entity_id,
                    )
                    await self._async_heater_turn_on(keepalive=True)
            elif (self.ac_mode and too_hot) or (not self.ac_mode and too_cold):
                # Make sure it's past the `cycle_cooldown` before turning on
                if self._last_toggled_time + self.cycle_cooldown <= now or force:
                    _LOGGER.debug("Turning on heater %s", self.heater_entity_id)
                    await self._async_heater_turn_on()
                elif self._check_callback is None:
                    _LOGGER.debug(
                        "Cooldown time not reached, check again at %s",
                        self._last_toggled_time + self.cycle_cooldown,
                    )
                    self._check_callback = async_call_later(
                        self.hass,
                        now - self._last_toggled_time + self.cycle_cooldown,
                        self._async_timer_control_heating,
                    )
            elif called_by_timer:
                # This is a keep-alive call, so ensure it's off
                _LOGGER.debug(
                    "Keep-alive - Turning off heater %s", self.heater_entity_id
                )
                await self._async_heater_turn_off(keepalive=True)