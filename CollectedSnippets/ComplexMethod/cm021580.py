async def test_logbook_humanify_automation_triggered_event(hass: HomeAssistant) -> None:
    """Test humanifying Automation Trigger event."""
    hass.config.components.add("recorder")
    await async_setup_component(hass, automation.DOMAIN, {})
    await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    event1, event2 = mock_humanify(
        hass,
        [
            MockRow(
                EVENT_AUTOMATION_TRIGGERED,
                {ATTR_ENTITY_ID: "automation.hello", ATTR_NAME: "Hello Automation"},
            ),
            MockRow(
                EVENT_AUTOMATION_TRIGGERED,
                {
                    ATTR_ENTITY_ID: "automation.bye",
                    ATTR_NAME: "Bye Automation",
                    ATTR_SOURCE: "source of trigger",
                },
            ),
        ],
    )

    assert event1["name"] == "Hello Automation"
    assert event1["domain"] == "automation"
    assert event1["message"] == "triggered"
    assert event1["entity_id"] == "automation.hello"

    assert event2["name"] == "Bye Automation"
    assert event2["domain"] == "automation"
    assert event2["message"] == "triggered by source of trigger"
    assert event2["entity_id"] == "automation.bye"