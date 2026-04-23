async def test_create_auth(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test create auth command works."""
    client = await hass_ws_client(hass)
    user = MockUser().add_to_hass(hass)

    assert len(user.credentials) == 0

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth_provider/homeassistant/create",
            "user_id": user.id,
            "username": "test-user2",
            "password": "test-pass",
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    assert len(user.credentials) == 1
    creds = user.credentials[0]
    assert creds.auth_provider_type == "homeassistant"
    assert creds.auth_provider_id is None
    assert creds.data == {"username": "test-user2"}
    assert prov_ha.STORAGE_KEY in hass_storage
    entry = hass_storage[prov_ha.STORAGE_KEY]["data"]["users"][1]
    assert entry["username"] == "test-user2"