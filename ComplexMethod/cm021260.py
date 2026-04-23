async def test_invalid_username_password(
    hass: HomeAssistant, aiohttp_client: ClientSessionGenerator
) -> None:
    """Test we cannot get flows in progress."""
    client = await async_setup_auth(hass, aiohttp_client)
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

    # Incorrect username
    with patch(
        "homeassistant.components.auth.login_flow.process_wrong_login"
    ) as mock_process_wrong_login:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "wrong-user",
                "password": "test-pass",
            },
        )

    assert resp.status == HTTPStatus.OK
    step = await resp.json()
    assert len(mock_process_wrong_login.mock_calls) == 1

    assert step["step_id"] == "init"
    assert step["errors"]["base"] == "invalid_auth"

    # Incorrect password
    with patch(
        "homeassistant.components.auth.login_flow.process_wrong_login"
    ) as mock_process_wrong_login:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "test-user",
                "password": "wrong-pass",
            },
        )

    assert resp.status == HTTPStatus.OK
    step = await resp.json()
    assert len(mock_process_wrong_login.mock_calls) == 1

    assert step["step_id"] == "init"
    assert step["errors"]["base"] == "invalid_auth"

    # Incorrect username and invalid redirect URI fails on wrong login
    with patch(
        "homeassistant.components.auth.login_flow.process_wrong_login"
    ) as mock_process_wrong_login:
        resp = await client.post(
            f"/auth/login_flow/{step['flow_id']}",
            json={
                "client_id": CLIENT_ID,
                "username": "wrong-user",
                "password": "test-pass",
            },
        )

    assert resp.status == HTTPStatus.OK
    step = await resp.json()
    assert len(mock_process_wrong_login.mock_calls) == 1

    assert step["step_id"] == "init"
    assert step["errors"]["base"] == "invalid_auth"