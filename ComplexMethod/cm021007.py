async def test_ws_list(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    schedule_setup: Callable[..., Coroutine[Any, Any, bool]],
) -> None:
    """Test listing via WS."""
    assert await schedule_setup()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 1
    assert result["from_storage"][ATTR_NAME] == "from storage"
    assert result["from_storage"][CONF_FRIDAY] == [
        {CONF_FROM: "17:00:00", CONF_TO: "23:59:59", CONF_DATA: {"party_level": "epic"}}
    ]
    assert result["from_storage"][CONF_SATURDAY] == [
        {CONF_FROM: "00:00:00", CONF_TO: "23:59:59"}
    ]
    assert result["from_storage"][CONF_SUNDAY] == [
        {CONF_FROM: "00:00:00", CONF_TO: "24:00:00", CONF_DATA: {"entry": "VIPs only"}}
    ]
    assert "from_yaml" not in result