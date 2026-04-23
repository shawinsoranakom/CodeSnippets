def start_timer(
        self,
        device_id: str | None,
        hours: int | None,
        minutes: int | None,
        seconds: int | None,
        language: str,
        name: str | None = None,
        conversation_command: str | None = None,
        conversation_agent_id: str | None = None,
    ) -> str:
        """Start a timer."""
        if (not conversation_command) and (device_id is None):
            raise ValueError("Conversation command must be set if no device id")

        if (not conversation_command) and (
            (device_id is None) or (not self.is_timer_device(device_id))
        ):
            raise TimersNotSupportedError(device_id)

        total_seconds = 0
        if hours is not None:
            total_seconds += 60 * 60 * hours

        if minutes is not None:
            total_seconds += 60 * minutes

        if seconds is not None:
            total_seconds += seconds

        timer_id = ulid_util.ulid_now()
        created_at = time.monotonic_ns()
        timer = TimerInfo(
            id=timer_id,
            name=name,
            start_hours=hours,
            start_minutes=minutes,
            start_seconds=seconds,
            seconds=total_seconds,
            language=language,
            device_id=device_id,
            created_at=created_at,
            updated_at=created_at,
            conversation_command=conversation_command,
            conversation_agent_id=conversation_agent_id,
        )

        # Fill in area/floor info
        device_registry = dr.async_get(self.hass)
        if device_id and (device := device_registry.async_get(device_id)):
            timer.area_id = device.area_id
            area_registry = ar.async_get(self.hass)
            if device.area_id and (
                area := area_registry.async_get_area(device.area_id)
            ):
                timer.area_name = _normalize_name(area.name)
                timer.floor_id = area.floor_id

        self.timers[timer_id] = timer
        self.timer_tasks[timer_id] = self.hass.async_create_background_task(
            self._wait_for_timer(timer_id, total_seconds, created_at),
            name=f"Timer {timer_id}",
        )

        if (not timer.conversation_command) and (timer.device_id in self.handlers):
            self.handlers[timer.device_id](TimerEventType.STARTED, timer)
        _LOGGER.debug(
            "Timer started: id=%s, name=%s, hours=%s, minutes=%s, seconds=%s, device_id=%s",
            timer_id,
            name,
            hours,
            minutes,
            seconds,
            device_id,
        )

        return timer_id