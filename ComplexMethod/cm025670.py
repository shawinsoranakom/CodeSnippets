def _parse_event(event: dict[str, Any]) -> Event:
    """Parse an ical event from a home assistant event dictionary."""
    if rrule := event.get(EVENT_RRULE):
        event[EVENT_RRULE] = Recur.from_rrule(rrule)

    # This function is called with new events created in the local timezone,
    # however ical library does not properly return recurrence_ids for
    # start dates with a timezone. For now, ensure any datetime is stored as a
    # floating local time to ensure we still apply proper local timezone rules.
    # This can be removed when ical is updated with a new recurrence_id format
    # https://github.com/home-assistant/core/issues/87759
    for key in (EVENT_START, EVENT_END):
        if (
            (value := event[key])
            and isinstance(value, datetime)
            and value.tzinfo is not None
        ):
            event[key] = dt_util.as_local(value).replace(tzinfo=None)
    # UNTIL in the rrule must be floating (timezone-naive) to match the
    # floating dtstart used by the ical library. Strip tzinfo from UNTIL
    # if present, converting to local time first.
    if (rrule_obj := event.get(EVENT_RRULE)) and isinstance(rrule_obj, Recur):
        if isinstance(rrule_obj.until, datetime) and rrule_obj.until.tzinfo is not None:
            rrule_obj.until = dt_util.as_local(rrule_obj.until).replace(tzinfo=None)

    try:
        return Event(**event)
    except CalendarParseError as err:
        _LOGGER.debug("Error parsing event input fields: %s (%s)", event, str(err))
        raise vol.Invalid("Error parsing event input fields") from err