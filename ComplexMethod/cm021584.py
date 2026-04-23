async def test_trigger_condition_implicit_id(
    hass: HomeAssistant, calls: list[ServiceCall]
) -> None:
    """Test triggers."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": [
                    {"trigger": "event", "event_type": "test_event1"},
                    {"trigger": "event", "event_type": "test_event2"},
                    {"trigger": "event", "event_type": "test_event3"},
                ],
                "action": {
                    "choose": [
                        {
                            "conditions": {"condition": "trigger", "id": [0, "2"]},
                            "sequence": {
                                "action": "test.automation",
                                "data": {"param": "one"},
                            },
                        },
                        {
                            "conditions": {"condition": "trigger", "id": "1"},
                            "sequence": {
                                "action": "test.automation",
                                "data": {"param": "two"},
                            },
                        },
                    ]
                },
            }
        },
    )

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    assert len(calls) == 1
    assert calls[-1].data.get("param") == "one"

    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    assert len(calls) == 2
    assert calls[-1].data.get("param") == "two"

    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    assert len(calls) == 3
    assert calls[-1].data.get("param") == "one"