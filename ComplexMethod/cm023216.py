async def test_actions(
    hass: HomeAssistant,
    client: Client,
    climate_radio_thermostat_ct100_plus: Node,
    integration: ConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test actions."""
    node = climate_radio_thermostat_ct100_plus
    driver = client.driver
    assert driver
    device_id = get_device_id(driver, node)
    device = device_registry.async_get_device(identifiers={device_id})
    assert device

    climate = entity_registry.async_get("climate.z_wave_thermostat")
    assert climate

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_refresh_value",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "refresh_value",
                        "device_id": device.id,
                        "entity_id": climate.id,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_ping",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "ping",
                        "device_id": device.id,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_value",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "set_value",
                        "device_id": device.id,
                        "command_class": 112,
                        "property": 1,
                        "value": 1,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_config_parameter",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "set_config_parameter",
                        "device_id": device.id,
                        "endpoint": 0,
                        "parameter": 1,
                        "bitmask": None,
                        "subtype": "3 (Beeper)",
                        "value": 1,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_config_parameter_no_endpoint",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "set_config_parameter",
                        "device_id": device.id,
                        "parameter": 1,
                        "bitmask": None,
                        "subtype": "3 (Beeper)",
                        "value": 1,
                    },
                },
            ]
        },
    )

    with patch("zwave_js_server.model.node.Node.async_poll_value") as mock_call:
        hass.bus.async_fire("test_event_refresh_value")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 1
        assert args[0].value_id == "13-64-1-mode"

    # Call action a second time to confirm that it works (this was previously a bug)
    with patch("zwave_js_server.model.node.Node.async_poll_value") as mock_call:
        hass.bus.async_fire("test_event_refresh_value")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 1
        assert args[0].value_id == "13-64-1-mode"

    with patch("zwave_js_server.model.node.Node.async_ping") as mock_call:
        hass.bus.async_fire("test_event_ping")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 0

    with patch("zwave_js_server.model.node.Node.async_set_value") as mock_call:
        hass.bus.async_fire("test_event_set_value")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 2
        assert args[0] == "13-112-0-1"
        assert args[1] == 1

    with patch(
        "homeassistant.components.zwave_js.services.async_set_config_parameter"
    ) as mock_call:
        hass.bus.async_fire("test_event_set_config_parameter")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 3
        assert args[0].node_id == 13
        assert args[1] == 1
        assert args[2] == 1

    with patch(
        "homeassistant.components.zwave_js.services.async_set_config_parameter"
    ) as mock_call:
        hass.bus.async_fire("test_event_set_config_parameter_no_endpoint")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 3
        assert args[0].node_id == 13
        assert args[1] == 1
        assert args[2] == 1