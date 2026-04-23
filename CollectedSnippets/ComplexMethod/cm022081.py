async def test_climate_cloud(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_cloud_config_entry: MockConfigEntry,
    mock_adax_cloud: AsyncMock,
) -> None:
    """Test states of the (cloud) Climate entity."""
    await setup_integration(hass, mock_cloud_config_entry)
    mock_adax_cloud.fetch_rooms_info.assert_called_once()

    assert len(hass.states.async_entity_ids(Platform.CLIMATE)) == 1
    entity_id = hass.states.async_entity_ids(Platform.CLIMATE)[0]

    state = hass.states.get(entity_id)

    assert state
    assert state.state == HVACMode.HEAT
    assert (
        state.attributes[ATTR_TEMPERATURE] == CLOUD_DEVICE_DATA[0]["targetTemperature"]
    )
    assert (
        state.attributes[ATTR_CURRENT_TEMPERATURE]
        == CLOUD_DEVICE_DATA[0]["temperature"]
    )

    mock_adax_cloud.fetch_rooms_info.side_effect = Exception()
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE