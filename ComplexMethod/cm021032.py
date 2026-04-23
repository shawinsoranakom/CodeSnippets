async def test_deep_sleep_added_after_setup(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test deep sleep added after setup."""
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=[
            BinarySensorInfo(
                object_id="test",
                key=1,
                name="test",
            ),
        ],
        states=[
            BinarySensorState(key=1, state=True, missing_state=False),
        ],
        device_info={"has_deep_sleep": False},
    )

    entity_id = "binary_sensor.test_test"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON

    await mock_device.mock_disconnect(expected_disconnect=True)

    # No deep sleep, should be unavailable
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    await mock_device.mock_connect()

    # reconnect, should be available
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON

    await mock_device.mock_disconnect(expected_disconnect=True)
    new_device_info = DeviceInfo(
        **{**asdict(mock_device.device_info), "has_deep_sleep": True}
    )
    mock_device.client.device_info = AsyncMock(return_value=new_device_info)
    mock_device.client.device_info_and_list_entities = AsyncMock(
        return_value=(
            new_device_info,
            mock_device.client.list_entities_services.return_value[0],
            mock_device.client.list_entities_services.return_value[1],
        )
    )
    mock_device.device_info = new_device_info

    await mock_device.mock_connect()

    # Now disconnect that deep sleep is set in device info
    await mock_device.mock_disconnect(expected_disconnect=True)

    # Deep sleep, should be available
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON