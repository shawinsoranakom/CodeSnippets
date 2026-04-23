async def test_storage_persists_preview_feature_across_calls(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test that storage persists preview feature state across multiple calls."""
    hass.config.components.add("kitchen_sink")
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    assert "core.labs" not in hass_storage

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

    assert_stored_labs_data(
        hass_storage,
        [{"domain": "kitchen_sink", "preview_feature": "special_repair"}],
    )

    # List preview features - should show enabled
    await client.send_json_auto_id({"type": "labs/list"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["features"][0]["enabled"] is True

    # Disable preview feature
    await client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "kitchen_sink",
            "preview_feature": "special_repair",
            "enabled": False,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]

    assert_stored_labs_data(
        hass_storage,
        [],
    )

    # List preview features - should show disabled
    await client.send_json_auto_id({"type": "labs/list"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["features"][0]["enabled"] is False