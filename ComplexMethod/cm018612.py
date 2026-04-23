async def test_websocket_update_preview_feature_enable(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test enabling a preview feature via WebSocket."""
    # Load kitchen_sink integration
    hass.config.components.add("kitchen_sink")
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    assert "core.labs" not in hass_storage

    # Track events
    events = []

    def event_listener(event):
        events.append(event)

    hass.bus.async_listen(EVENT_LABS_UPDATED, event_listener)

    # Enable the preview feature
    await client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        }
    )
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] is None

    # Verify event was fired
    await hass.async_block_till_done()
    assert len(events) == 1
    assert events[0].data["domain"] == "kitchen_sink"
    assert events[0].data["preview_feature"] == "special_repair"
    assert events[0].data["enabled"] is True

    # Verify feature is now enabled
    assert async_is_preview_feature_enabled(hass, "kitchen_sink", "special_repair")

    assert_stored_labs_data(
        hass_storage,
        [{"domain": "kitchen_sink", "preview_feature": "special_repair"}],
    )