async def test_switch_dnd(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_amazon_devices_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test switching DND."""
    await setup_integration(hass, mock_config_entry)

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_OFF

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    assert mock_amazon_devices_client.set_do_not_disturb.call_count == 1

    device_data = deepcopy(TEST_DEVICE_1)
    device_data.sensors = {
        "dnd": AmazonDeviceSensor(
            name="dnd",
            value=True,
            error=False,
            error_msg=None,
            error_type=None,
            scale=None,
        ),
        "temperature": AmazonDeviceSensor(
            name="temperature",
            value="22.5",
            error=False,
            error_msg=None,
            error_type=None,
            scale="CELSIUS",
        ),
    }
    mock_amazon_devices_client.get_devices_data.return_value = {
        TEST_DEVICE_1_SN: device_data
    }

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    device_data.sensors = {
        "dnd": AmazonDeviceSensor(
            name="dnd",
            value=False,
            error=False,
            error_msg=None,
            error_type=None,
            scale=None,
        ),
        "temperature": AmazonDeviceSensor(
            name="temperature",
            value="22.5",
            error=False,
            error_msg=None,
            error_type=None,
            scale="CELSIUS",
        ),
    }
    mock_amazon_devices_client.get_devices_data.return_value = {
        TEST_DEVICE_1_SN: device_data
    }

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert mock_amazon_devices_client.set_do_not_disturb.call_count == 2
    assert (state := hass.states.get(ENTITY_ID))
    assert state.state == STATE_OFF