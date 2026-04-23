async def test_get_config_parameters(
    hass: HomeAssistant, multisensor_6, integration, hass_ws_client: WebSocketGenerator
) -> None:
    """Test the get config parameters websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)
    node = multisensor_6
    device = get_device(hass, node)

    # Test getting configuration parameter values
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/get_config_parameters",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]

    assert len(result) == 61
    key = "52-112-0-2"
    assert result[key]["property"] == 2
    assert result[key]["property_key"] is None
    assert result[key]["endpoint"] == 0
    assert result[key]["configuration_value_type"] == "enumerated"
    assert result[key]["metadata"]["states"]
    assert (
        result[key]["metadata"]["description"]
        == "Stay awake for 10 minutes at power on"
    )
    assert result[key]["metadata"]["label"] == "Stay Awake in Battery Mode"
    assert result[key]["metadata"]["type"] == "number"
    assert result[key]["metadata"]["min"] == 0
    assert result[key]["metadata"]["max"] == 1
    assert result[key]["metadata"]["unit"] is None
    assert result[key]["metadata"]["writeable"] is True
    assert result[key]["metadata"]["readable"] is True
    assert result[key]["metadata"]["default"] == 0
    assert result[key]["value"] == 0

    key = "52-112-0-201-255"
    assert result[key]["property_key"] == 255

    # Test getting non-existent node config params fails
    await ws_client.send_json(
        {
            ID: 5,
            TYPE: "zwave_js/get_config_parameters",
            DEVICE_ID: "fake_device",
        }
    )
    msg = await ws_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Test sending command with not loaded entry fails
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json(
        {
            ID: 6,
            TYPE: "zwave_js/get_config_parameters",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED