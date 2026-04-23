def _find_timer(
    hass: HomeAssistant,
    device_id: str | None,
    slots: dict[str, Any],
    find_filter: FindTimerFilter | None = None,
) -> TimerInfo:
    """Match a single timer with constraints or raise an error."""
    timer_manager: TimerManager = hass.data[TIMER_DATA]

    # Ignore delayed command timers
    matching_timers: list[TimerInfo] = [
        t for t in timer_manager.timers.values() if not t.conversation_command
    ]
    has_filter = False

    if find_filter:
        # Filter by active state
        has_filter = True
        if find_filter == FindTimerFilter.ONLY_ACTIVE:
            matching_timers = [t for t in matching_timers if t.is_active]
        elif find_filter == FindTimerFilter.ONLY_INACTIVE:
            matching_timers = [t for t in matching_timers if not t.is_active]

        if len(matching_timers) == 1:
            # Only 1 match
            return matching_timers[0]

    # Search by name first
    name: str | None = None
    if "name" in slots:
        has_filter = True
        name = slots["name"]["value"]
        assert name is not None
        name_norm = _normalize_name(name)

        matching_timers = [t for t in matching_timers if t.name_normalized == name_norm]
        if len(matching_timers) == 1:
            # Only 1 match
            return matching_timers[0]

    # Search by area name
    area_name: str | None = None
    if "area" in slots:
        has_filter = True
        area_name = slots["area"]["value"]
        assert area_name is not None
        area_name_norm = _normalize_name(area_name)

        matching_timers = [t for t in matching_timers if t.area_name == area_name_norm]
        if len(matching_timers) == 1:
            # Only 1 match
            return matching_timers[0]

    # Use starting time to disambiguate
    start_hours: int | None = None
    if "start_hours" in slots:
        start_hours = int(slots["start_hours"]["value"])

    start_minutes: int | None = None
    if "start_minutes" in slots:
        start_minutes = int(slots["start_minutes"]["value"])

    start_seconds: int | None = None
    if "start_seconds" in slots:
        start_seconds = int(slots["start_seconds"]["value"])

    if (
        (start_hours is not None)
        or (start_minutes is not None)
        or (start_seconds is not None)
    ):
        has_filter = True
        matching_timers = [
            t
            for t in matching_timers
            if (t.start_hours == start_hours)
            and (t.start_minutes == start_minutes)
            and (t.start_seconds == start_seconds)
        ]

        if len(matching_timers) == 1:
            # Only 1 match remaining
            return matching_timers[0]

    if (not has_filter) and (len(matching_timers) == 1):
        # Only 1 match remaining with no filter
        return matching_timers[0]

    # Use device id
    if matching_timers and device_id:
        matching_device_timers = [
            t for t in matching_timers if (t.device_id == device_id)
        ]
        if len(matching_device_timers) == 1:
            # Only 1 match remaining
            return matching_device_timers[0]

        # Try area/floor
        device_registry = dr.async_get(hass)
        area_registry = ar.async_get(hass)
        if (
            (device := device_registry.async_get(device_id))
            and device.area_id
            and (area := area_registry.async_get_area(device.area_id))
        ):
            # Try area
            matching_area_timers = [
                t for t in matching_timers if (t.area_id == area.id)
            ]
            if len(matching_area_timers) == 1:
                # Only 1 match remaining
                return matching_area_timers[0]

            # Try floor
            matching_floor_timers = [
                t for t in matching_timers if (t.floor_id == area.floor_id)
            ]
            if len(matching_floor_timers) == 1:
                # Only 1 match remaining
                return matching_floor_timers[0]

    if matching_timers:
        raise MultipleTimersMatchedError

    _LOGGER.warning(
        "Timer not found: name=%s, area=%s, hours=%s, minutes=%s, seconds=%s, device_id=%s",
        name,
        area_name,
        start_hours,
        start_minutes,
        start_seconds,
        device_id,
    )

    raise TimerNotFoundError