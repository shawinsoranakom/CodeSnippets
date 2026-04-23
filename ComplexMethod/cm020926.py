async def test_wlan_switches(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry_setup: MockConfigEntry,
    mock_websocket_message: WebsocketMessageMock,
    wlan_payload: list[dict[str, Any]],
) -> None:
    """Test control of UniFi WLAN availability."""
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 1

    # Validate state object
    assert hass.states.get("switch.ssid_1_enabled").state == STATE_ON

    # Update state object
    wlan = deepcopy(wlan_payload[0])
    wlan["enabled"] = False
    mock_websocket_message(message=MessageKey.WLAN_CONF_UPDATED, data=wlan)
    await hass.async_block_till_done()
    assert hass.states.get("switch.ssid_1_enabled").state == STATE_OFF

    # Disable WLAN
    aioclient_mock.clear_requests()
    aioclient_mock.put(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/rest/wlanconf/{wlan['_id']}",
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.ssid_1_enabled"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[0][2] == {"enabled": False}

    # Enable WLAN
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {"entity_id": "switch.ssid_1_enabled"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[1][2] == {"enabled": True}