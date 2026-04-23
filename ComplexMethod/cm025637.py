async def async_create_event(entity: GoogleCalendarEntity, call: ServiceCall) -> None:
    """Add a new event to calendar."""
    start: DateOrDatetime | None = None
    end: DateOrDatetime | None = None
    hass = entity.hass

    if EVENT_IN in call.data:
        if EVENT_IN_DAYS in call.data[EVENT_IN]:
            now = datetime.now().date()

            start_in = now + timedelta(days=call.data[EVENT_IN][EVENT_IN_DAYS])
            end_in = start_in + timedelta(days=1)

            start = DateOrDatetime(date=start_in)
            end = DateOrDatetime(date=end_in)

        elif EVENT_IN_WEEKS in call.data[EVENT_IN]:
            now = datetime.now().date()

            start_in = now + timedelta(weeks=call.data[EVENT_IN][EVENT_IN_WEEKS])
            end_in = start_in + timedelta(days=1)

            start = DateOrDatetime(date=start_in)
            end = DateOrDatetime(date=end_in)

    elif EVENT_START_DATE in call.data and EVENT_END_DATE in call.data:
        start = DateOrDatetime(date=call.data[EVENT_START_DATE])
        end = DateOrDatetime(date=call.data[EVENT_END_DATE])

    elif EVENT_START_DATETIME in call.data and EVENT_END_DATETIME in call.data:
        start_dt = call.data[EVENT_START_DATETIME]
        end_dt = call.data[EVENT_END_DATETIME]
        start = DateOrDatetime(date_time=start_dt, timezone=str(hass.config.time_zone))
        end = DateOrDatetime(date_time=end_dt, timezone=str(hass.config.time_zone))

    if start is None or end is None:
        raise ValueError("Missing required fields to set start or end date/datetime")

    event = Event(
        summary=call.data[EVENT_SUMMARY],
        description=call.data[EVENT_DESCRIPTION],
        start=start,
        end=end,
    )
    if location := call.data.get(EVENT_LOCATION):
        event.location = location
    try:
        await cast(
            CalendarSyncUpdateCoordinator, entity.coordinator
        ).sync.api.async_create_event(
            entity.calendar_id,
            event,
        )
    except ApiException as err:
        raise HomeAssistantError(str(err)) from err
    entity.async_write_ha_state()