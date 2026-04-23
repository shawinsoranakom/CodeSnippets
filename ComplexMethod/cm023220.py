async def test_reset_meter_action(
    hass: HomeAssistant,
    client: Client,
    aeon_smart_switch_6: Node,
    integration: ConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test reset_meter action."""
    node = aeon_smart_switch_6
    driver = client.driver
    assert driver
    device_id = get_device_id(driver, node)
    device = device_registry.async_get_device(identifiers={device_id})
    assert device
    sensor = entity_registry.async_get("sensor.smart_switch_6_electric_consumed_kwh")
    assert sensor

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_reset_meter",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "reset_meter",
                        "device_id": device.id,
                        "entity_id": sensor.id,
                    },
                },
            ]
        },
    )

    with patch(
        "zwave_js_server.model.endpoint.Endpoint.async_invoke_cc_api"
    ) as mock_call:
        hass.bus.async_fire("test_event_reset_meter")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 2
        assert args[0] == CommandClass.METER
        assert args[1] == "reset"