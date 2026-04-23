async def test_onboarding_user(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    hass_client_no_auth: ClientSessionGenerator,
    area_registry: ar.AreaRegistry,
) -> None:
    """Test creating a new user."""
    # Create an existing area to mimic an integration creating an area
    # before onboarding is done.
    area_registry.async_create("Living Room")

    assert await async_setup_component(hass, "person", {})
    assert await async_setup_component(hass, "onboarding", {})
    await hass.async_block_till_done()

    cur_users = len(await hass.auth.async_get_users())
    client = await hass_client_no_auth()

    resp = await client.post(
        "/api/onboarding/users",
        json={
            "client_id": CLIENT_ID,
            "name": "Test Name",
            "username": "test-user",
            "password": "test-pass",
            "language": "en",
        },
    )

    assert resp.status == 200
    assert const.STEP_USER in hass_storage[const.DOMAIN]["data"]["done"]

    data = await resp.json()
    assert "auth_code" in data

    users = await hass.auth.async_get_users()
    assert len(await hass.auth.async_get_users()) == cur_users + 1
    user = next((user for user in users if user.name == "Test Name"), None)
    assert user is not None
    assert len(user.credentials) == 1
    assert user.credentials[0].data["username"] == "test-user"
    assert len(hass.data["person"][1].async_items()) == 1

    # Validate refresh token 1
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": data["auth_code"],
        },
    )

    assert resp.status == 200
    tokens = await resp.json()

    assert hass.auth.async_validate_access_token(tokens["access_token"]) is not None

    # Validate created areas
    assert len(area_registry.areas) == 3
    assert sorted(area.name for area in area_registry.async_list_areas()) == [
        "Bedroom",
        "Kitchen",
        "Living Room",
    ]