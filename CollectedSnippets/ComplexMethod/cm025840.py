def _update_status(self) -> None:
        """Update status itself."""
        super()._update_status()

        value = self.data.value

        if isinstance(value, time):
            local_now = datetime.now(
                tz=dt_util.get_time_zone(self.coordinator.hass.config.time_zone)
            )
            self._device_state = (
                self.coordinator.data[self._device_state_id].value
                if self._device_state_id in self.coordinator.data
                else None
            )
            if value in [0, None, time.min] or (
                self._device_state == "power_off"
                and self.entity_description.key
                in [TimerProperty.REMAIN, TimerProperty.TOTAL]
            ):
                # Reset to None when power_off
                value = None
            elif self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
                if self.entity_description.key in TIME_SENSOR_DESC:
                    # Set timestamp for absolute time
                    value = local_now.replace(hour=value.hour, minute=value.minute)
                else:
                    # Set timestamp for delta
                    event_data = timedelta(
                        hours=value.hour, minutes=value.minute, seconds=value.second
                    )
                    new_time = (
                        (local_now - event_data)
                        if self.entity_description.key == TimerProperty.RUNNING
                        else (local_now + event_data)
                    )
                    # The remain_time may change during the wash/dry operation depending on various reasons.
                    # If there is a diff of more than 60sec, the new timestamp is used
                    if (
                        parse_native_value := dt_util.parse_datetime(
                            str(self.native_value)
                        )
                    ) is None or abs(new_time - parse_native_value) > timedelta(
                        seconds=60
                    ):
                        value = new_time
                    else:
                        value = self.native_value
            elif self.entity_description.device_class == SensorDeviceClass.DURATION:
                # Set duration
                value = self._get_duration(
                    value, self.entity_description.native_unit_of_measurement
                )
        self._attr_native_value = value

        if (data_unit := self._get_unit_of_measurement(self.data.unit)) is not None:
            # For different from description's unit
            self._attr_native_unit_of_measurement = data_unit

        _LOGGER.debug(
            "[%s:%s] update status: %s -> %s, options:%s, unit:%s",
            self.coordinator.device_name,
            self.property_id,
            self.data.value,
            self.native_value,
            self.options,
            self.native_unit_of_measurement,
        )