async def test_signicant_change(
    checker: significant_change.SignificantlyChangedChecker,
) -> None:
    """Test initialize helper works."""
    ent_id = "test_domain.test_entity"
    attrs = {ATTR_DEVICE_CLASS: SensorDeviceClass.BATTERY}

    assert checker.async_is_significant_change(State(ent_id, "100", attrs))

    # Same state is not significant.
    assert not checker.async_is_significant_change(State(ent_id, "100", attrs))

    # State under 5 difference is not significant. (per test mock)
    assert not checker.async_is_significant_change(State(ent_id, "96", attrs))

    # Make sure we always compare against last significant change
    assert checker.async_is_significant_change(State(ent_id, "95", attrs))

    # State turned unknown
    assert checker.async_is_significant_change(State(ent_id, STATE_UNKNOWN, attrs))

    # State turned unavailable
    assert checker.async_is_significant_change(State(ent_id, "100", attrs))
    assert checker.async_is_significant_change(State(ent_id, STATE_UNAVAILABLE, attrs))