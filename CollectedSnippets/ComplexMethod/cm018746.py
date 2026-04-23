async def test_enable_hdr_processing_select(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_device: MagicMock,
    mock_integration: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test enabling the HDR processing select (disabled by default)."""
    entry = entity_registry.async_get(HDR_PROCESSING_ENTITY_ID)
    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    hdr_sensor_entry = entity_registry.async_get(HDR_SENSOR_ENTITY_ID)
    assert hdr_sensor_entry is not None
    assert hdr_sensor_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    entity_registry.async_update_entity(HDR_SENSOR_ENTITY_ID, disabled_by=None)
    entity_registry.async_update_entity(HDR_PROCESSING_ENTITY_ID, disabled_by=None)
    await hass.config_entries.async_reload(mock_integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(HDR_PROCESSING_ENTITY_ID)
    assert state is not None
    assert state.state == "unknown"

    freezer.tick(timedelta(seconds=INTERVAL_FAST.seconds + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(HDR_PROCESSING_ENTITY_ID)
    assert state is not None
    assert state.state == "static"

    freezer.tick(timedelta(seconds=INTERVAL_FAST.seconds + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(HDR_PROCESSING_ENTITY_ID)
    assert state is not None
    assert state.state == "static"