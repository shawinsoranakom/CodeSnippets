async def test_node_metadata(
    hass: HomeAssistant,
    wallmote_central_scene,
    integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the node metadata websocket command."""
    entry = integration
    ws_client = await hass_ws_client(hass)

    node = wallmote_central_scene
    device = get_device(hass, node)
    await ws_client.send_json(
        {
            ID: 3,
            TYPE: "zwave_js/node_metadata",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()
    result = msg["result"]

    assert result[NODE_ID] == 35
    assert result["inclusion"] == (
        "To add the ZP3111 to the Z-Wave network (inclusion), place the Z-Wave "
        "primary controller into inclusion mode. Press the Program Switch of ZP3111 "
        "for sending the NIF. After sending NIF, Z-Wave will send the auto inclusion, "
        "otherwise, ZP3111 will go to sleep after 20 seconds."
    )
    assert result["exclusion"] == (
        "To remove the ZP3111 from the Z-Wave network (exclusion), place the Z-Wave "
        "primary controller into \u201cexclusion\u201d mode, and following its "
        "instruction to delete the ZP3111 to the controller. Press the Program Switch "
        "of ZP3111 once to be excluded."
    )
    assert result["reset"] == (
        "Remove cover to triggered tamper switch, LED flash once & send out Alarm "
        "Report. Press Program Switch 10 times within 10 seconds, ZP3111 will send "
        "the \u201cDevice Reset Locally Notification\u201d command and reset to the "
        "factory default. (Remark: This is to be used only in the case of primary "
        "controller being inoperable or otherwise unavailable.)"
    )
    assert result["manual"] == (
        "https://products.z-wavealliance.org/ProductManual/File?folder=&filename="
        "MarketCertificationFiles/2479/ZP3111-5_R2_20170316.pdf"
    )
    assert not result["wakeup"]
    assert (
        result["device_database_url"]
        == "https://devices.zwave-js.io/?jumpTo=0x0086:0x0002:0x0082:0.0"
    )

    # Test getting non-existent node fails
    await ws_client.send_json(
        {
            ID: 4,
            TYPE: "zwave_js/node_metadata",
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
            ID: 5,
            TYPE: "zwave_js/node_metadata",
            DEVICE_ID: device.id,
        }
    )
    msg = await ws_client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == ERR_NOT_LOADED