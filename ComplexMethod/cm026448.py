async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._sensor_entity_id, self._async_sensor_event
            )
        )
        self.async_on_remove(
            async_track_state_report_event(
                self.hass, self._sensor_entity_id, self._async_sensor_event
            )
        )
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, self._switch_entity_id, self._async_switch_event
            )
        )
        if self._keep_alive:
            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self._async_operate, self._keep_alive
                )
            )

        async def _async_startup(event: Event | None) -> None:
            """Init on startup."""
            sensor_state = self.hass.states.get(self._sensor_entity_id)
            if sensor_state is None or sensor_state.state in (
                STATE_UNKNOWN,
                STATE_UNAVAILABLE,
            ):
                _LOGGER.debug(
                    "The sensor state is %s, initialization is delayed",
                    sensor_state.state if sensor_state is not None else "None",
                )
                return

            await self._async_sensor_update(sensor_state)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

        if (old_state := await self.async_get_last_state()) is not None:
            if old_state.attributes.get(ATTR_MODE) == MODE_AWAY:
                self._is_away = True
                self._saved_target_humidity = self._target_humidity
                self._target_humidity = self._away_humidity or self._target_humidity
            if old_state.attributes.get(ATTR_HUMIDITY):
                self._target_humidity = int(old_state.attributes[ATTR_HUMIDITY])
            if old_state.attributes.get(ATTR_SAVED_HUMIDITY):
                self._saved_target_humidity = int(
                    old_state.attributes[ATTR_SAVED_HUMIDITY]
                )
            if old_state.state:
                self._state = old_state.state == STATE_ON
        if self._target_humidity is None:
            if self._device_class == HumidifierDeviceClass.HUMIDIFIER:
                self._target_humidity = self.min_humidity
            else:
                self._target_humidity = self.max_humidity
            _LOGGER.warning(
                "No previously saved humidity, setting to %s", self._target_humidity
            )
        if self._state is None:
            self._state = False

        await _async_startup(None)