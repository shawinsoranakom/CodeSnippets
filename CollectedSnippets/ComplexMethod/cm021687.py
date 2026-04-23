async def test_auth_get_access_token_expired(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the auth get access token function."""
    client_id = "client123"
    client_secret = "shhhhh"
    accept_grant_code = "abcdefg"
    refresh_token = "refresher"

    await run_auth_get_access_token(
        hass,
        aioclient_mock,
        -5,
        client_id,
        client_secret,
        accept_grant_code,
        refresh_token,
    )

    assert len(aioclient_mock.mock_calls) == 2
    calls = aioclient_mock.mock_calls

    auth_call_json = calls[0][2]
    token_call_json = calls[1][2]

    assert auth_call_json["grant_type"] == "authorization_code"
    assert auth_call_json["code"] == accept_grant_code
    assert auth_call_json[CONF_CLIENT_ID] == client_id
    assert auth_call_json[CONF_CLIENT_SECRET] == client_secret

    assert token_call_json["grant_type"] == "refresh_token"
    assert token_call_json["refresh_token"] == refresh_token
    assert token_call_json[CONF_CLIENT_ID] == client_id
    assert token_call_json[CONF_CLIENT_SECRET] == client_secret