async def test_logbook_humanify_script_started_event(hass: HomeAssistant) -> None:
    """Test humanifying script started event."""
    hass.config.components.add("recorder")
    await async_setup_component(hass, DOMAIN, {})
    await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    event1, event2 = mock_humanify(
        hass,
        [
            MockRow(
                EVENT_SCRIPT_STARTED,
                {ATTR_ENTITY_ID: "script.hello", ATTR_NAME: "Hello Script"},
            ),
            MockRow(
                EVENT_SCRIPT_STARTED,
                {ATTR_ENTITY_ID: "script.bye", ATTR_NAME: "Bye Script"},
            ),
        ],
    )

    assert event1["name"] == "Hello Script"
    assert event1["domain"] == "script"
    assert event1["message"] == "started"
    assert event1["entity_id"] == "script.hello"

    assert event2["name"] == "Bye Script"
    assert event2["domain"] == "script"
    assert event2["message"] == "started"
    assert event2["entity_id"] == "script.bye"