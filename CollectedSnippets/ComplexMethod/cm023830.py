async def test_change_radio_button_group(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, kpl_properties_data
) -> None:
    """Test changing an Insteon device's properties."""
    ws_client, devices = await _setup(
        hass, hass_ws_client, "33.33.33", kpl_properties_data
    )
    rb_groups = devices["33.33.33"].configuration[RADIO_BUTTON_GROUPS]

    # Make sure the baseline is correct
    assert rb_groups.value[0] == [4, 5]
    assert rb_groups.value[1] == [7, 8]

    # Add button 1 to the group
    new_groups_1 = [[1, 4, 5], [7, 8]]
    with patch.object(insteon.api.properties, "devices", devices):
        await ws_client.send_json(
            {
                ID: 2,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: RADIO_BUTTON_GROUPS,
                PROPERTY_VALUE: new_groups_1,
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert rb_groups.new_value[0] == [1, 4, 5]
        assert rb_groups.new_value[1] == [7, 8]

        new_groups_2 = [[1, 4], [7, 8]]
        await ws_client.send_json(
            {
                ID: 3,
                TYPE: "insteon/properties/change",
                DEVICE_ADDRESS: "33.33.33",
                PROPERTY_NAME: RADIO_BUTTON_GROUPS,
                PROPERTY_VALUE: new_groups_2,
            }
        )
        msg = await ws_client.receive_json()
        assert msg["success"]
        assert rb_groups.new_value[0] == [1, 4]
        assert rb_groups.new_value[1] == [7, 8]