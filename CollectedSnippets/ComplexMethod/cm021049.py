async def test_state_subscription(
    mock_client: APIClient,
    hass: HomeAssistant,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test ESPHome subscribes to state changes."""
    device = await mock_esphome_device(
        mock_client=mock_client,
    )
    await hass.async_block_till_done()
    hass.states.async_set("binary_sensor.test", "on", {"bool": True, "float": 3.0})
    device.mock_home_assistant_state_subscription("binary_sensor.test", None)
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == [
        call("binary_sensor.test", None, "on")
    ]
    mock_client.send_home_assistant_state.reset_mock()
    hass.states.async_set("binary_sensor.test", "off", {"bool": True, "float": 3.0})
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == [
        call("binary_sensor.test", None, "off")
    ]
    mock_client.send_home_assistant_state.reset_mock()
    device.mock_home_assistant_state_subscription("binary_sensor.test", "bool")
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == [
        call("binary_sensor.test", "bool", "on")
    ]
    mock_client.send_home_assistant_state.reset_mock()
    hass.states.async_set("binary_sensor.test", "off", {"bool": False, "float": 3.0})
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == [
        call("binary_sensor.test", "bool", "off")
    ]
    mock_client.send_home_assistant_state.reset_mock()
    device.mock_home_assistant_state_subscription("binary_sensor.test", "float")
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == [
        call("binary_sensor.test", "float", "3.0")
    ]
    mock_client.send_home_assistant_state.reset_mock()
    hass.states.async_set("binary_sensor.test", "on", {"bool": True, "float": 4.0})
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == [
        call("binary_sensor.test", None, "on"),
        call("binary_sensor.test", "bool", "on"),
        call("binary_sensor.test", "float", "4.0"),
    ]
    mock_client.send_home_assistant_state.reset_mock()
    hass.states.async_set("binary_sensor.test", "on", {})
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == []
    hass.states.async_remove("binary_sensor.test")
    await hass.async_block_till_done()
    assert mock_client.send_home_assistant_state.mock_calls == []