async def test_websocket_subscribe_feature_receives_updates(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that subscription receives updates when feature is toggled."""
    hass.config.components.add("kitchen_sink")
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "labs/subscribe",
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
        }
    )
    subscribe_msg = await client.receive_json()
    assert subscribe_msg["success"]
    subscription_id = subscribe_msg["id"]

    # Initial state event
    initial_event_msg = await client.receive_json()
    assert initial_event_msg["id"] == subscription_id
    assert initial_event_msg["type"] == "event"
    assert initial_event_msg["event"]["enabled"] is False

    await client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": True,
        }
    )

    # Update event arrives before the update result
    event_msg = await client.receive_json()
    assert event_msg["id"] == subscription_id
    assert event_msg["type"] == "event"
    assert event_msg["event"] == {
        "preview_feature": "special_repair",
        "domain": "kitchen_sink",
        "enabled": True,
        "is_built_in": True,
        "feedback_url": ANY,
        "learn_more_url": ANY,
        "report_issue_url": ANY,
    }

    update_msg = await client.receive_json()
    assert update_msg["success"]