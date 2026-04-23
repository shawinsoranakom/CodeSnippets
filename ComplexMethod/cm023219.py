async def test_lock_actions(
    hass: HomeAssistant,
    client: Client,
    lock_schlage_be469: Node,
    integration: ConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test actions for locks."""
    node = lock_schlage_be469
    driver = client.driver
    assert driver
    device_id = get_device_id(driver, node)
    device = device_registry.async_get_device(identifiers={device_id})
    assert device
    lock = entity_registry.async_get("lock.touchscreen_deadbolt")
    assert lock

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_clear_lock_usercode",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "clear_lock_usercode",
                        "device_id": device.id,
                        "entity_id": lock.id,
                        "code_slot": 1,
                    },
                },
                {
                    "trigger": {
                        "platform": "event",
                        "event_type": "test_event_set_lock_usercode",
                    },
                    "action": {
                        "domain": DOMAIN,
                        "type": "set_lock_usercode",
                        "device_id": device.id,
                        "entity_id": lock.id,
                        "code_slot": 1,
                        "usercode": "1234",
                    },
                },
            ]
        },
    )

    with patch("homeassistant.components.zwave_js.lock.clear_usercode") as mock_call:
        hass.bus.async_fire("test_event_clear_lock_usercode")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 2
        assert args[0].node_id == node.node_id
        assert args[1] == 1

    with patch("homeassistant.components.zwave_js.lock.set_usercode") as mock_call:
        hass.bus.async_fire("test_event_set_lock_usercode")
        await hass.async_block_till_done()
        mock_call.assert_called_once()
        args = mock_call.call_args_list[0][0]
        assert len(args) == 3
        assert args[0].node_id == node.node_id
        assert args[1] == 1
        assert args[2] == "1234"