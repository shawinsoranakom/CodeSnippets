async def test_poe_port_switches(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_websocket_message: WebsocketMessageMock,
    mock_websocket_state: WebsocketStateManager,
) -> None:
    """Test the update_items function with some clients."""
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2

    ent_reg_entry = entity_registry.async_get("sensor.mock_name_port_1_poe_power")
    assert ent_reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

    # Enable entity
    entity_registry.async_update_entity(
        entity_id="sensor.mock_name_port_1_poe_power", disabled_by=None
    )
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # Validate state object
    poe_sensor = hass.states.get("sensor.mock_name_port_1_poe_power")
    assert poe_sensor.state == "2.56"
    assert poe_sensor.attributes.get(ATTR_DEVICE_CLASS) == SensorDeviceClass.POWER

    # Update state object
    device_1 = deepcopy(DEVICE_1)
    device_1["port_table"][0]["poe_power"] = "5.12"
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.mock_name_port_1_poe_power").state == "5.12"

    # PoE is disabled
    device_1 = deepcopy(DEVICE_1)
    device_1["port_table"][0]["poe_mode"] = "off"
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.mock_name_port_1_poe_power").state == "0"

    # Availability signalling

    # Controller disconnects
    await mock_websocket_state.disconnect()
    assert (
        hass.states.get("sensor.mock_name_port_1_poe_power").state == STATE_UNAVAILABLE
    )

    # Controller reconnects
    await mock_websocket_state.reconnect()
    assert (
        hass.states.get("sensor.mock_name_port_1_poe_power").state != STATE_UNAVAILABLE
    )

    # Device gets disabled
    device_1["disabled"] = True
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert (
        hass.states.get("sensor.mock_name_port_1_poe_power").state == STATE_UNAVAILABLE
    )

    # Device gets re-enabled
    device_1["disabled"] = False
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.mock_name_port_1_poe_power")