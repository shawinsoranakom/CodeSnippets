async def test_auth_access_signed_path_with_refresh_token(
    hass: HomeAssistant,
    app: web.Application,
    aiohttp_client: ClientSessionGenerator,
    hass_access_token: str,
) -> None:
    """Test access with signed url."""
    app.router.add_post("/", mock_handler)
    app.router.add_get("/another_path", mock_handler)
    await async_setup_auth(hass, app)
    client = await aiohttp_client(app)

    refresh_token = hass.auth.async_validate_access_token(hass_access_token)

    signed_path = async_sign_path(
        hass, "/", timedelta(seconds=5), refresh_token_id=refresh_token.id
    )

    req = await client.head(signed_path)
    assert req.status == HTTPStatus.OK

    req = await client.get(signed_path)
    assert req.status == HTTPStatus.OK
    data = await req.json()
    assert data["user_id"] == refresh_token.user.id

    # Use signature on other path
    req = await client.head(f"/another_path?{signed_path.split('?')[1]}")
    assert req.status == HTTPStatus.UNAUTHORIZED

    req = await client.get(f"/another_path?{signed_path.split('?')[1]}")
    assert req.status == HTTPStatus.UNAUTHORIZED

    # We only allow GET and HEAD
    req = await client.post(signed_path)
    assert req.status == HTTPStatus.UNAUTHORIZED

    # Never valid as expired in the past.
    expired_signed_path = async_sign_path(
        hass, "/", timedelta(seconds=-5), refresh_token_id=refresh_token.id
    )

    req = await client.get(expired_signed_path)
    assert req.status == HTTPStatus.UNAUTHORIZED

    # refresh token gone should also invalidate signature
    hass.auth.async_remove_refresh_token(refresh_token)
    req = await client.get(signed_path)
    assert req.status == HTTPStatus.UNAUTHORIZED