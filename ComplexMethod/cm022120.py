async def test_service_call_create_logbook_entry(hass_: HomeAssistant) -> None:
    """Test if service call create log book entry."""
    calls = async_capture_events(hass_, logbook.EVENT_LOGBOOK_ENTRY)

    await hass_.services.async_call(
        logbook.DOMAIN,
        "log",
        {
            logbook.ATTR_NAME: "Alarm",
            logbook.ATTR_MESSAGE: "is triggered",
            logbook.ATTR_DOMAIN: "switch",
            logbook.ATTR_ENTITY_ID: "switch.test_switch",
        },
        True,
    )
    await hass_.services.async_call(
        logbook.DOMAIN,
        "log",
        {
            logbook.ATTR_NAME: "This entry",
            logbook.ATTR_MESSAGE: "has no domain or entity_id",
        },
        True,
    )
    # Logbook entry service call results in firing an event.
    # Our service call will unblock when the event listeners have been
    # scheduled. This means that they may not have been processed yet.
    await async_wait_recording_done(hass_)
    event_processor = EventProcessor(hass_, (EVENT_LOGBOOK_ENTRY,))

    events = list(
        event_processor.get_events(
            dt_util.utcnow() - timedelta(hours=1),
            dt_util.utcnow() + timedelta(hours=1),
        )
    )
    assert len(events) == 2

    assert len(calls) == 2
    first_call = calls[-2]

    assert first_call.data.get(logbook.ATTR_NAME) == "Alarm"
    assert first_call.data.get(logbook.ATTR_MESSAGE) == "is triggered"
    assert first_call.data.get(logbook.ATTR_DOMAIN) == "switch"
    assert first_call.data.get(logbook.ATTR_ENTITY_ID) == "switch.test_switch"

    last_call = calls[-1]

    assert last_call.data.get(logbook.ATTR_NAME) == "This entry"
    assert last_call.data.get(logbook.ATTR_MESSAGE) == "has no domain or entity_id"
    assert last_call.data.get(logbook.ATTR_DOMAIN) == "logbook"