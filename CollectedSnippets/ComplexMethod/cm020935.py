async def test_device_updates(
    hass: HomeAssistant, mock_websocket_message: WebsocketMessageMock
) -> None:
    """Test the update_items function with some devices."""
    device_1_state = hass.states.get("update.device_1_firmware")
    assert device_1_state.state == STATE_ON
    assert device_1_state.attributes[ATTR_IN_PROGRESS] is False

    # Simulate start of update

    device_1 = deepcopy(DEVICE_1)
    device_1["state"] = 4
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)

    device_1_state = hass.states.get("update.device_1_firmware")
    assert device_1_state.state == STATE_ON
    assert device_1_state.attributes[ATTR_INSTALLED_VERSION] == "4.0.42.10433"
    assert device_1_state.attributes[ATTR_LATEST_VERSION] == "4.3.17.11279"
    assert device_1_state.attributes[ATTR_IN_PROGRESS] is True

    # Simulate update finished

    device_1["state"] = 0
    device_1["version"] = "4.3.17.11279"
    device_1["upgradable"] = False
    del device_1["upgrade_to_firmware"]
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)

    device_1_state = hass.states.get("update.device_1_firmware")
    assert device_1_state.state == STATE_OFF
    assert device_1_state.attributes[ATTR_INSTALLED_VERSION] == "4.3.17.11279"
    assert device_1_state.attributes[ATTR_LATEST_VERSION] == "4.3.17.11279"
    assert device_1_state.attributes[ATTR_IN_PROGRESS] is False