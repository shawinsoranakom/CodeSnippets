async def test_bandwidth_sensors(
    hass: HomeAssistant,
    mock_websocket_message: WebsocketMessageMock,
    config_entry_options: MappingProxyType[str, Any],
    config_entry_setup: MockConfigEntry,
    client_payload: list[dict[str, Any]],
) -> None:
    """Verify that bandwidth sensors are working as expected."""
    # Verify state update
    wireless_client = deepcopy(client_payload[1])
    wireless_client["rx_bytes-r"] = 3456000000
    wireless_client["tx_bytes-r"] = 7891000000

    mock_websocket_message(message=MessageKey.CLIENT, data=wireless_client)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.wireless_client_rx").state == "3456.0"
    assert hass.states.get("sensor.wireless_client_tx").state == "7891.0"

    # Verify reset sensor after heartbeat expires

    new_time = dt_util.utcnow()
    wireless_client["last_seen"] = dt_util.as_timestamp(new_time)

    mock_websocket_message(message=MessageKey.CLIENT, data=wireless_client)
    await hass.async_block_till_done()

    with freeze_time(new_time):
        async_fire_time_changed(hass, new_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.wireless_client_rx").state == "3456.0"
    assert hass.states.get("sensor.wireless_client_tx").state == "7891.0"

    new_time += timedelta(
        seconds=(
            config_entry_setup.options.get(CONF_DETECTION_TIME, DEFAULT_DETECTION_TIME)
            + 1
        )
    )
    with freeze_time(new_time):
        async_fire_time_changed(hass, new_time)
        await hass.async_block_till_done()

    assert hass.states.get("sensor.wireless_client_rx").state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.wireless_client_tx").state == STATE_UNAVAILABLE

    # Disable option
    options = deepcopy(config_entry_options)
    options[CONF_ALLOW_BANDWIDTH_SENSORS] = False
    hass.config_entries.async_update_entry(config_entry_setup, options=options)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 1
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 0
    assert hass.states.get("sensor.wireless_client_rx") is None
    assert hass.states.get("sensor.wireless_client_tx") is None
    assert hass.states.get("sensor.wired_client_rx") is None
    assert hass.states.get("sensor.wired_client_tx") is None

    # Enable option
    options = deepcopy(config_entry_options)
    options[CONF_ALLOW_BANDWIDTH_SENSORS] = True
    hass.config_entries.async_update_entry(config_entry_setup, options=options)
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 5
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 4
    assert hass.states.get("sensor.wireless_client_rx")
    assert hass.states.get("sensor.wireless_client_tx")
    assert hass.states.get("sensor.wired_client_rx")
    assert hass.states.get("sensor.wired_client_tx")