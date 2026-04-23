def _async_handle_event(self, webhook_id: str, data: dict[str, str]) -> None:
        """Handle the Sleep as Android event."""

        if webhook_id == self.webhook_id and data[ATTR_EVENT] in (
            "alarm_snooze_clicked",
            "alarm_snooze_canceled",
            "alarm_skip_next",
            "show_skip_next_alarm",
            "alarm_rescheduled",
        ):
            if (
                self.entity_description.key is SleepAsAndroidSensor.NEXT_ALARM
                and (alarm_time := data.get(ATTR_VALUE1))
                and alarm_time.isnumeric()
            ):
                self._attr_native_value = datetime.fromtimestamp(
                    int(alarm_time) / 1000, tz=dt_util.get_default_time_zone()
                )
            if self.entity_description.key is SleepAsAndroidSensor.ALARM_LABEL and (
                label := data.get(ATTR_VALUE2, ALARM_LABEL_DEFAULT)
            ):
                self._attr_native_value = label

            if (
                data[ATTR_EVENT] == "alarm_rescheduled"
                and data.get(ATTR_VALUE1) is None
            ):
                self._attr_native_value = None

            self.async_write_ha_state()