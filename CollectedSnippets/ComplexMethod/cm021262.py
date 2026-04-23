async def test_ws_current_user(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_access_token: str
) -> None:
    """Test the current user command with Home Assistant creds."""
    assert await async_setup_component(hass, "auth", {})

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    user = refresh_token.user
    client = await hass_ws_client(hass, hass_access_token)

    await client.send_json({"id": 5, "type": "auth/current_user"})

    result = await client.receive_json()
    assert result["success"], result

    user_dict = result["result"]

    assert user_dict["name"] == user.name
    assert user_dict["id"] == user.id
    assert user_dict["is_owner"] == user.is_owner
    assert len(user_dict["credentials"]) == 1

    hass_cred = user_dict["credentials"][0]
    assert hass_cred["auth_provider_type"] == "homeassistant"
    assert hass_cred["auth_provider_id"] is None
    assert "data" not in hass_cred