async def test_websocket_event_data_structure(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that event data has correct structure."""
    hass.config.components.add("kitchen_sink")
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    events = []

    def event_listener(event):
        events.append(event)

    hass.bus.async_listen(EVENT_LABS_UPDATED, event_listener)

    # Enable a feature
    await client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        }
    )
    await client.receive_json()
    await hass.async_block_till_done()

    assert len(events) == 1
    event_data = events[0].data
    # Verify all required fields are present
    assert "domain" in event_data
    assert "preview_feature" in event_data
    assert "enabled" in event_data
    assert event_data["domain"] == "kitchen_sink"
    assert event_data["preview_feature"] == "special_repair"
    assert event_data["enabled"] is True
    assert isinstance(event_data["enabled"], bool)