async def test_auth_active_access_with_access_token_in_header(
    hass: HomeAssistant,
    app: web.Application,
    aiohttp_client: ClientSessionGenerator,
    hass_access_token: str,
) -> None:
    """Test access with access token in header."""
    token = hass_access_token
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)
    refresh_token = hass.auth.async_validate_access_token(hass_access_token)

    req = await client.get("/", headers={"Authorization": f"Bearer {token}"})
    assert req.status == HTTPStatus.OK
    assert await req.json() == {"user_id": refresh_token.user.id}

    req = await client.get("/", headers={"AUTHORIZATION": f"Bearer {token}"})
    assert req.status == HTTPStatus.OK
    assert await req.json() == {"user_id": refresh_token.user.id}

    req = await client.get("/", headers={"authorization": f"Bearer {token}"})
    assert req.status == HTTPStatus.OK
    assert await req.json() == {"user_id": refresh_token.user.id}

    req = await client.get("/", headers={"Authorization": token})
    assert req.status == HTTPStatus.UNAUTHORIZED

    req = await client.get("/", headers={"Authorization": f"BEARER {token}"})
    assert req.status == HTTPStatus.UNAUTHORIZED

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)
    refresh_token.user.is_active = False
    req = await client.get("/", headers={"Authorization": f"Bearer {token}"})
    assert req.status == HTTPStatus.UNAUTHORIZED