async def test_get_trigger_platform_registers_triggers(
    hass: HomeAssistant,
) -> None:
    """Test _async_get_trigger_platform registers triggers and notifies subscribers."""

    class MockTrigger(Trigger):
        """Mock trigger."""

        async def async_attach_runner(
            self, run_action: TriggerActionRunner
        ) -> CALLBACK_TYPE:
            return lambda: None

    async def async_get_triggers(
        hass: HomeAssistant,
    ) -> dict[str, type[Trigger]]:
        return {"trig_a": MockTrigger, "trig_b": MockTrigger}

    mock_integration(hass, MockModule("test"))
    mock_platform(hass, "test.trigger", Mock(async_get_triggers=async_get_triggers))

    subscriber_events: list[set[str]] = []

    async def subscriber(new_triggers: set[str]) -> None:
        subscriber_events.append(new_triggers)

    trigger.async_subscribe_platform_events(hass, subscriber)

    assert "test.trig_a" not in hass.data[TRIGGERS]
    assert "test.trig_b" not in hass.data[TRIGGERS]

    # First call registers all triggers from the platform and notifies subscribers
    await _async_get_trigger_platform(hass, "test.trig_a")

    assert hass.data[TRIGGERS]["test.trig_a"] == "test"
    assert hass.data[TRIGGERS]["test.trig_b"] == "test"
    assert len(subscriber_events) == 1
    assert subscriber_events[0] == {"test.trig_a", "test.trig_b"}

    # Subsequent calls are idempotent — no re-registration or re-notification
    await _async_get_trigger_platform(hass, "test.trig_a")
    await _async_get_trigger_platform(hass, "test.trig_b")
    assert len(subscriber_events) == 1