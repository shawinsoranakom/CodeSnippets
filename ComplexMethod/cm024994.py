async def test_config_entry(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test behavior of coordinator.entry."""
    entry = MockConfigEntry()

    # Explicit None is OK
    crd = update_coordinator.DataUpdateCoordinator[int](
        hass, _LOGGER, name="test", config_entry=None
    )
    assert crd.config_entry is None
    assert (
        "Detected that integration 'my_integration' relies on ContextVar"
        not in caplog.text
    )

    # Explicit entry is OK
    caplog.clear()
    crd = update_coordinator.DataUpdateCoordinator[int](
        hass, _LOGGER, name="test", config_entry=entry
    )
    assert crd.config_entry is entry
    assert (
        "Detected that integration 'my_integration' relies on ContextVar"
        not in caplog.text
    )

    # Explicit entry different from ContextVar not recommended, but should work
    another_entry = MockConfigEntry()
    caplog.clear()
    crd = update_coordinator.DataUpdateCoordinator[int](
        hass, _LOGGER, name="test", config_entry=another_entry
    )
    assert crd.config_entry is another_entry
    assert (
        "Detected that integration 'my_integration' relies on ContextVar"
        not in caplog.text
    )

    # Default without context should log a warning
    caplog.clear()
    crd = update_coordinator.DataUpdateCoordinator[int](hass, _LOGGER, name="test")
    assert crd.config_entry is None
    assert (
        "Detected that integration 'my_integration' relies on ContextVar, "
        "but should pass the config entry explicitly."
    ) in caplog.text

    # Default with context should log a warning
    caplog.clear()
    frame._REPORTED_INTEGRATIONS.clear()
    config_entries.current_entry.set(entry)
    crd = update_coordinator.DataUpdateCoordinator[int](hass, _LOGGER, name="test")
    assert (
        "Detected that integration 'my_integration' relies on ContextVar, "
        "but should pass the config entry explicitly."
    ) in caplog.text
    assert crd.config_entry is entry