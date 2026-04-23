async def test_actions_multiple_calls(
    hass: HomeAssistant,
    client: Client,
    climate_radio_thermostat_ct100_plus: Node,
    integration: ConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test actions can be called multiple times and still work."""
    node = climate_radio_thermostat_ct100_plus
    driver = client.driver
    assert driver
    device_id = get_device_id(driver, node)
    device = device_registry.async_get_device({device_id})
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
            ]
        },
    )

    # Trigger automation multiple times to confirm that it works each time
    for _ in range(5):
        with patch("zwave_js_server.model.node.Node.async_poll_value") as mock_call:
            hass.bus.async_fire("test_event_refresh_value")
            await hass.async_block_till_done()
            mock_call.assert_called_once()
            args = mock_call.call_args_list[0][0]
            assert len(args) == 1
            assert args[0].value_id == "13-64-1-mode"