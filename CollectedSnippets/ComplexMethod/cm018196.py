async def test_get_config(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    hass_admin_user: MockUser,
    local_only_user: bool,
    forbidden_keys: list[str],
) -> None:
    """Test get_config command."""
    hass_admin_user.local_only = local_only_user
    await websocket_client.send_json_auto_id({"type": "get_config"})

    msg = await websocket_client.receive_json()
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    result = msg["result"]
    ignore_order_keys = (
        "components",
        "allowlist_external_dirs",
        "whitelist_external_dirs",
        "allowlist_external_urls",
    )
    config = hass.config.as_dict()

    for key in ignore_order_keys:
        if key in result:
            result[key] = set(result[key])
            config[key] = set(config[key])

    for key in forbidden_keys:
        assert key in config
        config.pop(key)

    assert result == config