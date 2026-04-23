async def test_get_properties(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    kpl_properties_data,
    iolinc_properties_data,
) -> None:
    """Test getting an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )
    devices.fill_properties("44.44.44", iolinc_properties_data)

    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "33.33.33",
                SHOW_ADVANCED: False,
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert len(msg["result"]["properties"]) == 18

        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: False,
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert len(msg["result"]["properties"]) == 6

        await ws_client.send_json(
            {
                ID: 4,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "33.33.33",
                SHOW_ADVANCED: True,
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert len(msg["result"]["properties"]) == 69

        await ws_client.send_json(
            {
                ID: 5,
                TYPE: "insteon/properties/get",
                DEVICE_ADDRESS: "44.44.44",
                SHOW_ADVANCED: True,
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert len(msg["result"]["properties"]) == 14