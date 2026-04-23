async def test_get_condition_platform_registers_conditions(
    hass: HomeAssistant,
) -> None:
    """Test _async_get_condition_platform registers conditions and notifies subscribers."""

    class MockCondition(Condition):
        """Mock condition."""

        @classmethod
        async def async_validate_config(
            cls, hass: HomeAssistant, config: ConfigType
        ) -> ConfigType:
            return config

        async def async_get_checker(self) -> ConditionChecker:
            return lambda **kwargs: True

    async def async_get_conditions(
        hass: HomeAssistant,
    ) -> dict[str, type[Condition]]:
        return {"cond_a": MockCondition, "cond_b": MockCondition}

    mock_integration(hass, MockModule("test"))
    mock_platform(
        hass, "test.condition", Mock(async_get_conditions=async_get_conditions)
    )

    subscriber_events: list[set[str]] = []

    async def subscriber(new_conditions: set[str]) -> None:
        subscriber_events.append(new_conditions)

    condition.async_subscribe_platform_events(hass, subscriber)

    assert "test.cond_a" not in hass.data[CONDITIONS]
    assert "test.cond_b" not in hass.data[CONDITIONS]

    # First call registers all conditions from the platform and notifies subscribers
    await _async_get_condition_platform(hass, "test.cond_a")

    assert hass.data[CONDITIONS]["test.cond_a"] == "test"
    assert hass.data[CONDITIONS]["test.cond_b"] == "test"
    assert len(subscriber_events) == 1
    assert subscriber_events[0] == {"test.cond_a", "test.cond_b"}

    # Subsequent calls are idempotent — no re-registration or re-notification
    await _async_get_condition_platform(hass, "test.cond_a")
    await _async_get_condition_platform(hass, "test.cond_b")
    assert len(subscriber_events) == 1