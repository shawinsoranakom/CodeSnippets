async def test_create_user_group(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_access_token: str
) -> None:
    """Test create user with a group."""
    client = await hass_ws_client(hass, hass_access_token)

    cur_users = len(await hass.auth.async_get_users())

    await client.send_json(
        {
            "id": 5,
            "type": "config/auth/create",
            "name": "Paulus",
            "group_ids": ["system-admin"],
        }
    )

    result = await client.receive_json()
    assert result["success"], result
    assert len(await hass.auth.async_get_users()) == cur_users + 1
    data_user = result["result"]["user"]
    user = await hass.auth.async_get_user(data_user["id"])
    assert user is not None
    assert user.name == data_user["name"]
    assert user.is_active
    assert user.groups[0].id == "system-admin"
    assert user.is_admin
    assert not user.is_owner
    assert not user.system_generated