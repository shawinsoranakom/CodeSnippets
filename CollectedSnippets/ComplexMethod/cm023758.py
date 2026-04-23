async def test_device_registry_info(
    hass: HomeAssistant,
    satellite_device: SatelliteDevice,
    satellite_config_entry: ConfigEntry,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test info in device registry."""

    # Satellite uses config entry id since only one satellite per entry is
    # supported.
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, satellite_config_entry.entry_id)}
    )
    assert device is not None
    assert device.name == "Test Satellite"
    assert device.area_id == area_registry.async_get_area_by_name("Office").id

    # Check associated entities
    assist_in_progress_id = satellite_device.get_assist_in_progress_entity_id(hass)
    assert assist_in_progress_id
    assist_in_progress_state = hass.states.get(assist_in_progress_id)
    # assist_in_progress binary sensor is disabled
    assert assist_in_progress_state is None

    muted_id = satellite_device.get_muted_entity_id(hass)
    assert muted_id
    muted_state = hass.states.get(muted_id)
    assert muted_state is not None
    assert muted_state.state == STATE_OFF

    pipeline_entity_id = satellite_device.get_pipeline_entity_id(hass)
    assert pipeline_entity_id
    pipeline_state = hass.states.get(pipeline_entity_id)
    assert pipeline_state is not None
    assert pipeline_state.state == OPTION_PREFERRED