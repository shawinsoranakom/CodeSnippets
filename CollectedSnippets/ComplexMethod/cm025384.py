def set_alarm(
        self,
        alarm_id: int,
        time: datetime.datetime | None = None,
        volume: float | None = None,
        enabled: bool | None = None,
        include_linked_zones: bool | None = None,
    ) -> None:
        """Set the alarm clock on the player."""
        alarm: alarms.Alarm | None = None
        for one_alarm in alarms.get_alarms(self.coordinator.soco):
            if one_alarm.alarm_id == str(alarm_id):
                alarm = one_alarm
        if alarm is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_alarm_id",
                translation_placeholders={
                    "alarm_id": str(alarm_id),
                },
            )
        if time is not None:
            alarm.start_time = time
        if volume is not None:
            alarm.volume = int(volume * 100)
        if enabled is not None:
            alarm.enabled = enabled
        if include_linked_zones is not None:
            alarm.include_linked_zones = include_linked_zones
        alarm.save()