def _find_timers(
    hass: HomeAssistant, device_id: str | None, slots: dict[str, Any]
) -> list[TimerInfo]:
    """Match multiple timers with constraints or raise an error."""
    timer_manager: TimerManager = hass.data[TIMER_DATA]

    # Ignore delayed command timers
    matching_timers: list[TimerInfo] = [
        t for t in timer_manager.timers.values() if not t.conversation_command
    ]

    # Filter by name first
    name: str | None = None
    if "name" in slots:
        name = slots["name"]["value"]
        assert name is not None
        name_norm = _normalize_name(name)

        matching_timers = [t for t in matching_timers if t.name_normalized == name_norm]
        if not matching_timers:
            # No matches
            return matching_timers

    # Filter by area name
    area_name: str | None = None
    if "area" in slots:
        area_name = slots["area"]["value"]
        assert area_name is not None
        area_name_norm = _normalize_name(area_name)

        matching_timers = [t for t in matching_timers if t.area_name == area_name_norm]
        if not matching_timers:
            # No matches
            return matching_timers

    # Use starting time to filter, if present
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
        matching_timers = [
            t
            for t in matching_timers
            if (t.start_hours == start_hours)
            and (t.start_minutes == start_minutes)
            and (t.start_seconds == start_seconds)
        ]
        if not matching_timers:
            # No matches
            return matching_timers

    if not device_id:
        # Can't order using area/floor
        return matching_timers

    # Use device id to order remaining timers
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if (device is None) or (device.area_id is None):
        return matching_timers

    area_registry = ar.async_get(hass)
    area = area_registry.async_get_area(device.area_id)
    if area is None:
        return matching_timers

    def area_floor_sort(timer: TimerInfo) -> int:
        """Sort by area, then floor."""
        if timer.area_id == area.id:
            return -2

        if timer.floor_id == area.floor_id:
            return -1

        return 0

    matching_timers.sort(key=area_floor_sort)

    return matching_timers