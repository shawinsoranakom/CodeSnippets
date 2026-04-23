def sun(
    hass: HomeAssistant,
    before: str | None = None,
    after: str | None = None,
    before_offset: timedelta | None = None,
    after_offset: timedelta | None = None,
) -> bool:
    """Test if current time matches sun requirements."""
    utcnow = dt_util.utcnow()
    today = dt_util.as_local(utcnow).date()
    before_offset = before_offset or timedelta(0)
    after_offset = after_offset or timedelta(0)

    sunrise = get_astral_event_date(hass, SUN_EVENT_SUNRISE, today)
    sunset = get_astral_event_date(hass, SUN_EVENT_SUNSET, today)

    has_sunrise_condition = SUN_EVENT_SUNRISE in (before, after)
    has_sunset_condition = SUN_EVENT_SUNSET in (before, after)

    after_sunrise = today > dt_util.as_local(cast(datetime, sunrise)).date()
    if after_sunrise and has_sunrise_condition:
        tomorrow = today + timedelta(days=1)
        sunrise = get_astral_event_date(hass, SUN_EVENT_SUNRISE, tomorrow)

    after_sunset = today > dt_util.as_local(cast(datetime, sunset)).date()
    if after_sunset and has_sunset_condition:
        tomorrow = today + timedelta(days=1)
        sunset = get_astral_event_date(hass, SUN_EVENT_SUNSET, tomorrow)

    # Special case: before sunrise OR after sunset
    # This will handle the very rare case in the polar region when the sun rises/sets
    # but does not set/rise.
    # However this entire condition does not handle those full days of darkness
    # or light, the following should be used instead:
    #
    #    condition:
    #      condition: state
    #      entity_id: sun.sun
    #      state: 'above_horizon' (or 'below_horizon')
    #
    if before == SUN_EVENT_SUNRISE and after == SUN_EVENT_SUNSET:
        wanted_time_before = cast(datetime, sunrise) + before_offset
        condition_trace_update_result(wanted_time_before=wanted_time_before)
        wanted_time_after = cast(datetime, sunset) + after_offset
        condition_trace_update_result(wanted_time_after=wanted_time_after)
        return utcnow < wanted_time_before or utcnow > wanted_time_after

    if sunrise is None and has_sunrise_condition:
        # There is no sunrise today
        condition_trace_set_result(False, message="no sunrise today")
        return False

    if sunset is None and has_sunset_condition:
        # There is no sunset today
        condition_trace_set_result(False, message="no sunset today")
        return False

    if before == SUN_EVENT_SUNRISE:
        wanted_time_before = cast(datetime, sunrise) + before_offset
        condition_trace_update_result(wanted_time_before=wanted_time_before)
        if utcnow > wanted_time_before:
            return False

    if before == SUN_EVENT_SUNSET:
        wanted_time_before = cast(datetime, sunset) + before_offset
        condition_trace_update_result(wanted_time_before=wanted_time_before)
        if utcnow > wanted_time_before:
            return False

    if after == SUN_EVENT_SUNRISE:
        wanted_time_after = cast(datetime, sunrise) + after_offset
        condition_trace_update_result(wanted_time_after=wanted_time_after)
        if utcnow < wanted_time_after:
            return False

    if after == SUN_EVENT_SUNSET:
        wanted_time_after = cast(datetime, sunset) + after_offset
        condition_trace_update_result(wanted_time_after=wanted_time_after)
        if utcnow < wanted_time_after:
            return False

    return True