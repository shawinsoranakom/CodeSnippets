async def test_wlan_client_sensors(
    hass: HomeAssistant,
    config_entry_factory: ConfigEntryFactoryType,
    mock_websocket_message: WebsocketMessageMock,
    mock_websocket_state: WebsocketStateManager,
    client_payload: list[dict[str, Any]],
) -> None:
    """Verify that WLAN client sensors are working as expected."""
    client_payload += [
        {
            "essid": "SSID 1",
            "is_wired": False,
            "last_seen": dt_util.as_timestamp(dt_util.utcnow()),
            "mac": "00:00:00:00:00:01",
            "name": "Wireless client",
            "oui": "Producer",
            "rx_bytes-r": 2345000000,
            "tx_bytes-r": 6789000000,
        },
        {
            "essid": "SSID 2",
            "is_wired": False,
            "last_seen": dt_util.as_timestamp(dt_util.utcnow()),
            "mac": "00:00:00:00:00:02",
            "name": "Wireless client2",
            "oui": "Producer2",
            "rx_bytes-r": 2345000000,
            "tx_bytes-r": 6789000000,
        },
    ]
    await config_entry_factory()

    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 1

    # Validate state object
    assert hass.states.get("sensor.ssid_1_clients").state == "1"

    # Verify state update - increasing number
    wireless_client_1 = client_payload[0]
    wireless_client_1["essid"] = "SSID 1"
    mock_websocket_message(message=MessageKey.CLIENT, data=wireless_client_1)
    wireless_client_2 = client_payload[1]
    wireless_client_2["essid"] = "SSID 1"
    mock_websocket_message(message=MessageKey.CLIENT, data=wireless_client_2)
    await hass.async_block_till_done()

    ssid_1 = hass.states.get("sensor.ssid_1_clients")
    assert ssid_1.state == "1"

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    ssid_1 = hass.states.get("sensor.ssid_1_clients")
    assert ssid_1.state == "2"

    # Verify state update - decreasing number

    wireless_client_1["essid"] = "SSID"
    mock_websocket_message(message=MessageKey.CLIENT, data=wireless_client_1)

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    ssid_1 = hass.states.get("sensor.ssid_1_clients")
    assert ssid_1.state == "1"

    # Verify state update - decreasing number

    wireless_client_2["last_seen"] = 0
    mock_websocket_message(message=MessageKey.CLIENT, data=wireless_client_2)

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    ssid_1 = hass.states.get("sensor.ssid_1_clients")
    assert ssid_1.state == "0"

    # Availability signalling

    # Controller disconnects
    await mock_websocket_state.disconnect()
    assert hass.states.get("sensor.ssid_1_clients").state == STATE_UNAVAILABLE

    # Controller reconnects
    await mock_websocket_state.reconnect()
    assert hass.states.get("sensor.ssid_1_clients").state == "0"

    # WLAN gets disabled
    wlan_1 = deepcopy(WLAN)
    wlan_1["enabled"] = False
    mock_websocket_message(message=MessageKey.WLAN_CONF_UPDATED, data=wlan_1)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.ssid_1_clients").state == STATE_UNAVAILABLE

    # WLAN gets re-enabled
    wlan_1["enabled"] = True
    mock_websocket_message(message=MessageKey.WLAN_CONF_UPDATED, data=wlan_1)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.ssid_1_clients").state == "0"