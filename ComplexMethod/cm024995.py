async def test_config_entry_custom_integration(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test behavior of coordinator.entry for custom integrations."""
    entry = MockConfigEntry(domain="custom_integration")

    # Default without context should be None
    crd = update_coordinator.DataUpdateCoordinator[int](hass, _LOGGER, name="test")

    assert crd.config_entry is None
    # Should not log any warnings about ContextVar usage for custom integrations
    frame_records = [
        record
        for record in caplog.records
        if record.name == "homeassistant.helpers.frame"
        and record.levelno >= logging.WARNING
    ]
    assert len(frame_records) == 0

    # Explicit None is OK
    caplog.clear()

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
    frame_records = [
        record
        for record in caplog.records
        if record.name == "homeassistant.helpers.frame"
        and record.levelno >= logging.WARNING
    ]
    assert len(frame_records) == 0

    # set ContextVar
    config_entries.current_entry.set(entry)

    # Default with ContextVar should match the ContextVar
    caplog.clear()

    crd = update_coordinator.DataUpdateCoordinator[int](hass, _LOGGER, name="test")

    assert crd.config_entry is entry
    frame_records = [
        record
        for record in caplog.records
        if record.name == "homeassistant.helpers.frame"
        and record.levelno >= logging.WARNING
    ]
    assert len(frame_records) == 0

    # Explicit entry different from ContextVar not recommended, but should work
    another_entry = MockConfigEntry()
    caplog.clear()

    crd = update_coordinator.DataUpdateCoordinator[int](
        hass, _LOGGER, name="test", config_entry=another_entry
    )

    assert crd.config_entry is another_entry
    frame_records = [
        record
        for record in caplog.records
        if record.name == "homeassistant.helpers.frame"
        and record.levelno >= logging.WARNING
    ]
    assert len(frame_records) == 0