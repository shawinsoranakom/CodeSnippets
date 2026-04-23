async def test_login_new_user_and_trying_refresh_token(
    hass: HomeAssistant, aiohttp_client: ClientSessionGenerator
) -> None:
    """Test logging in with new user and refreshing tokens."""
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    resp = await client.post(
        "/auth/login_flow",
        json={
            "client_id": CLIENT_ID,
            "handler": ["insecure_example", None],
            "redirect_uri": CLIENT_REDIRECT_URI,
        },
    )
    assert resp.status == HTTPStatus.OK
    step = await resp.json()

    resp = await client.post(
        f"/auth/login_flow/{step['flow_id']}",
        json={
            "client_id": CLIENT_ID,
            "username": "test-user",
            "password": "test-pass",
        },
    )

    assert resp.status == HTTPStatus.OK
    step = await resp.json()
    code = step["result"]

    # Exchange code for tokens
    resp = await client.post(
        "/auth/token",
        data={"client_id": CLIENT_ID, "grant_type": "authorization_code", "code": code},
    )

    assert resp.status == HTTPStatus.OK
    tokens = await resp.json()

    assert hass.auth.async_validate_access_token(tokens["access_token"]) is not None
    assert tokens["ha_auth_provider"] == "insecure_example"

    # Use refresh token to get more tokens.
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert resp.status == HTTPStatus.OK
    tokens = await resp.json()
    assert "refresh_token" not in tokens
    assert hass.auth.async_validate_access_token(tokens["access_token"]) is not None

    # Test using access token to hit API.
    resp = await client.get("/api/")
    assert resp.status == HTTPStatus.UNAUTHORIZED

    resp = await client.get(
        "/api/", headers={"authorization": f"Bearer {tokens['access_token']}"}
    )
    assert resp.status == HTTPStatus.OK