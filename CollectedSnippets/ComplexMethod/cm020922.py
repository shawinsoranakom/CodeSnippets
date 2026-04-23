async def test_remove_switches(
    hass: HomeAssistant, mock_websocket_message: WebsocketMessageMock
) -> None:
    """Test the update_items function with some clients."""
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 2

    assert hass.states.get("switch.block_client_2_blocked") is not None
    assert hass.states.get("switch.unifi_network_block_media_streaming") is not None

    mock_websocket_message(message=MessageKey.CLIENT_REMOVED, data=[UNBLOCKED])
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 1

    assert hass.states.get("switch.block_client_2_blocked") is None
    assert hass.states.get("switch.unifi_network_block_media_streaming") is not None

    mock_websocket_message(data=DPI_GROUP_REMOVED_EVENT)
    await hass.async_block_till_done()

    assert hass.states.get("switch.unifi_network_block_media_streaming") is None
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 0