async def test_bandwidth_port_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry_setup: MockConfigEntry,
    config_entry_options: MappingProxyType[str, Any],
    mock_websocket_message: WebsocketMessageMock,
    device_payload: list[dict[str, Any]],
) -> None:
    """Verify that port bandwidth sensors are working as expected."""
    assert len(hass.states.async_all()) == 5
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2

    p1rx_reg_entry = entity_registry.async_get("sensor.mock_name_port_1_rx")
    assert p1rx_reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

    p1tx_reg_entry = entity_registry.async_get("sensor.mock_name_port_1_tx")
    assert p1tx_reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

    # Enable entity
    entity_registry.async_update_entity(
        entity_id="sensor.mock_name_port_1_rx", disabled_by=None
    )
    entity_registry.async_update_entity(
        entity_id="sensor.mock_name_port_1_tx", disabled_by=None
    )
    entity_registry.async_update_entity(
        entity_id="sensor.mock_name_port_2_rx", disabled_by=None
    )
    entity_registry.async_update_entity(
        entity_id="sensor.mock_name_port_2_tx", disabled_by=None
    )
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # Validate state object
    assert len(hass.states.async_all()) == 9
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 6

    # Verify sensor state
    assert hass.states.get("sensor.mock_name_port_1_rx").state == "0.009208"
    assert hass.states.get("sensor.mock_name_port_1_tx").state == "0.040888"
    assert hass.states.get("sensor.mock_name_port_2_rx").state == "0.012288"
    assert hass.states.get("sensor.mock_name_port_2_tx").state == "0.02892"

    # Verify state update
    device_1 = device_payload[0]
    device_1["port_table"][0]["rx_bytes-r"] = 3456000000
    device_1["port_table"][0]["tx_bytes-r"] = 7891000000

    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.mock_name_port_1_rx").state == "27648.0"
    assert hass.states.get("sensor.mock_name_port_1_tx").state == "63128.0"

    # Disable option
    options = config_entry_options.copy()
    options[CONF_ALLOW_BANDWIDTH_SENSORS] = False
    hass.config_entries.async_update_entry(config_entry_setup, options=options)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 5
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 2

    assert hass.states.get("sensor.mock_name_uptime")
    assert hass.states.get("sensor.mock_name_state")
    assert hass.states.get("sensor.mock_name_port_1_rx") is None
    assert hass.states.get("sensor.mock_name_port_1_tx") is None
    assert hass.states.get("sensor.mock_name_port_2_rx") is None
    assert hass.states.get("sensor.mock_name_port_2_tx") is None