async def mqtt_async_added_to_hass(self) -> None:
        """Restore state for entities with expire_after set."""
        last_state: State | None
        last_sensor_data: SensorExtraStoredData | None
        if (
            (_expire_after := self._expire_after) is not None
            and _expire_after > 0
            and (last_state := await self.async_get_last_state()) is not None
            and last_state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE]
            and (last_sensor_data := await self.async_get_last_sensor_data())
            is not None
            # We might have set up a trigger already after subscribing from
            # MqttEntity.async_added_to_hass(), then we should not restore state
            and not self._expiration_trigger
        ):
            expiration_at = last_state.last_changed + timedelta(seconds=_expire_after)
            remain_seconds = (expiration_at - dt_util.utcnow()).total_seconds()

            if remain_seconds <= 0:
                # Skip reactivating the sensor
                _LOGGER.debug("Skip state recovery after reload for %s", self.entity_id)
                return
            self._expired = False
            self._attr_native_value = last_sensor_data.native_value

            self._expiration_trigger = async_call_later(
                self.hass, remain_seconds, self._value_is_expired
            )
            _LOGGER.debug(
                (
                    "State recovered after reload for %s, remaining time before"
                    " expiring %s"
                ),
                self.entity_id,
                remain_seconds,
            )