async def test_ws_refresh_tokens(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_access_token: str
) -> None:
    """Test fetching refresh token metadata."""
    assert await async_setup_component(hass, "auth", {"http": {}})

    ws_client = await hass_ws_client(hass, hass_access_token)

    await ws_client.send_json({"id": 5, "type": "auth/refresh_tokens"})

    result = await ws_client.receive_json()
    assert result["success"], result
    assert len(result["result"]) == 1
    token = result["result"][0]
    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    assert token["id"] == refresh_token.id
    assert token["type"] == refresh_token.token_type
    assert token["client_id"] == refresh_token.client_id
    assert token["client_name"] == refresh_token.client_name
    assert token["client_icon"] == refresh_token.client_icon
    assert token["created_at"] == refresh_token.created_at.isoformat()
    assert token["is_current"] is True
    assert token["last_used_at"] == refresh_token.last_used_at.isoformat()
    assert token["last_used_ip"] == refresh_token.last_used_ip
    assert token["auth_provider_type"] == "homeassistant"