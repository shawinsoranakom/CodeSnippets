async def test_dynamic_device(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_amazon_devices_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test device added dynamically."""

    entity_id_1 = "binary_sensor.echo_test_connectivity"
    entity_id_2 = "binary_sensor.echo_test_2_connectivity"

    mock_amazon_devices_client.get_devices_data.return_value = {
        TEST_DEVICE_1_SN: TEST_DEVICE_1,
    }

    await setup_integration(hass, mock_config_entry)

    assert (state := hass.states.get(entity_id_1))
    assert state.state == STATE_ON

    assert not hass.states.get(entity_id_2)

    mock_amazon_devices_client.get_devices_data.return_value = {
        TEST_DEVICE_1_SN: TEST_DEVICE_1,
        TEST_DEVICE_2_SN: TEST_DEVICE_2,
    }

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id_1))
    assert state.state == STATE_ON

    assert (state := hass.states.get(entity_id_2))
    assert state.state == STATE_ON