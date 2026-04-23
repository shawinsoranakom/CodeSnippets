async def test_port_forwarding_switches(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry_setup: MockConfigEntry,
    mock_websocket_message: WebsocketMessageMock,
    port_forward_payload: list[dict[str, Any]],
) -> None:
    """Test control of UniFi port forwarding."""
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 1

    # Validate state object
    assert hass.states.get("switch.unifi_network_plex").state == STATE_ON

    # Update state object
    data = port_forward_payload[0].copy()
    data["enabled"] = False
    mock_websocket_message(message=MessageKey.PORT_FORWARD_UPDATED, data=data)
    await hass.async_block_till_done()
    assert hass.states.get("switch.unifi_network_plex").state == STATE_OFF

    # Disable port forward
    aioclient_mock.clear_requests()
    aioclient_mock.put(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/rest/portforward/{data['_id']}",
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.unifi_network_plex"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 1
    data = port_forward_payload[0].copy()
    data["enabled"] = False
    assert aioclient_mock.mock_calls[0][2] == data

    # Enable port forward
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {"entity_id": "switch.unifi_network_plex"},
        blocking=True,
    )
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[1][2] == port_forward_payload[0]

    # Remove entity on deleted message
    mock_websocket_message(
        message=MessageKey.PORT_FORWARD_DELETED, data=port_forward_payload[0]
    )
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 0