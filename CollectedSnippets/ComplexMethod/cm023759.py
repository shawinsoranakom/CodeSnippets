async def test_remove_device_registry_entry(
    hass: HomeAssistant,
    satellite_device: SatelliteDevice,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test removing a device registry entry."""

    # Check associated entities
    assist_in_progress_id = satellite_device.get_assist_in_progress_entity_id(hass)
    assert assist_in_progress_id
    # assist_in_progress binary sensor is disabled
    assert hass.states.get(assist_in_progress_id) is None

    muted_id = satellite_device.get_muted_entity_id(hass)
    assert muted_id
    assert hass.states.get(muted_id) is not None

    pipeline_entity_id = satellite_device.get_pipeline_entity_id(hass)
    assert pipeline_entity_id
    assert hass.states.get(pipeline_entity_id) is not None

    # Remove
    device_registry.async_remove_device(satellite_device.device_id)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Everything should be gone
    assert hass.states.get(assist_in_progress_id) is None
    assert hass.states.get(muted_id) is None
    assert hass.states.get(pipeline_entity_id) is None