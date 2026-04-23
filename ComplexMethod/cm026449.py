async def _async_operate(
        self, time: datetime | None = None, force: bool = False
    ) -> None:
        """Check if we need to turn humidifying on or off."""
        async with self._humidity_lock:
            if not self._active and None not in (
                self._cur_humidity,
                self._target_humidity,
            ):
                self._active = True
                force = True
                _LOGGER.debug(
                    (
                        "Obtained current and target humidity. "
                        "Generic hygrostat active. %s, %s"
                    ),
                    self._cur_humidity,
                    self._target_humidity,
                )

            if not self._active or not self._state:
                return

            if not force and time is None:
                # If the `force` argument is True, we
                # ignore `min_cycle_duration`.
                # If the `time` argument is not none, we were invoked for
                # keep-alive purposes, and `min_cycle_duration` is irrelevant.
                if self._min_cycle_duration:
                    if self._is_device_active:
                        current_state = STATE_ON
                    else:
                        current_state = STATE_OFF
                    long_enough = condition.state(
                        self.hass,
                        self._switch_entity_id,
                        current_state,
                        self._min_cycle_duration,
                    )
                    if not long_enough:
                        return

            if force:
                # Ignore the tolerance when switched on manually
                dry_tolerance: float = 0
                wet_tolerance: float = 0
            else:
                dry_tolerance = self._dry_tolerance
                wet_tolerance = self._wet_tolerance

            if TYPE_CHECKING:
                assert self._target_humidity is not None
                assert self._cur_humidity is not None
            too_dry = self._target_humidity - self._cur_humidity >= dry_tolerance
            too_wet = self._cur_humidity - self._target_humidity >= wet_tolerance
            if self._is_device_active:
                if (
                    self._device_class == HumidifierDeviceClass.HUMIDIFIER and too_wet
                ) or (
                    self._device_class == HumidifierDeviceClass.DEHUMIDIFIER and too_dry
                ):
                    _LOGGER.debug("Turning off humidifier %s", self._switch_entity_id)
                    await self._async_device_turn_off()
                elif time is not None:
                    # The time argument is passed only in keep-alive case
                    await self._async_device_turn_on()
            elif (
                self._device_class == HumidifierDeviceClass.HUMIDIFIER and too_dry
            ) or (self._device_class == HumidifierDeviceClass.DEHUMIDIFIER and too_wet):
                _LOGGER.debug("Turning on humidifier %s", self._switch_entity_id)
                await self._async_device_turn_on()
            elif time is not None:
                # The time argument is passed only in keep-alive case
                await self._async_device_turn_off()