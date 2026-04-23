async def test_trigger_service_ignoring_condition(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture, calls: list[ServiceCall]
) -> None:
    """Test triggers."""
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "test",
                "trigger": [{"platform": "event", "event_type": "test_event"}],
                "conditions": {
                    "condition": "numeric_state",
                    "entity_id": "non.existing",
                    "above": "1",
                },
                "action": {"action": "test.automation"},
            }
        },
    )

    caplog.clear()
    caplog.set_level(logging.WARNING)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 0

    assert len(caplog.record_tuples) == 1
    assert caplog.record_tuples[0][1] == logging.WARNING

    await hass.services.async_call(
        "automation", "trigger", {"entity_id": "automation.test"}, blocking=True
    )
    assert len(calls) == 1

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.test", "skip_condition": True},
        blocking=True,
    )
    assert len(calls) == 2

    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.test", "skip_condition": False},
        blocking=True,
    )
    assert len(calls) == 2