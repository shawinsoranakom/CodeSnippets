async def test_token_refresh_success(
    integration_setup: Callable[[], Awaitable[bool]],
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    setup_credentials: None,
) -> None:
    """Test where token is expired and the refresh attempt succeeds."""

    assert config_entry.data["token"]["access_token"] == FAKE_ACCESS_TOKEN

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json=SERVER_ACCESS_TOKEN,
    )

    assert await integration_setup()
    assert config_entry.state is ConfigEntryState.LOADED

    # Verify token request and that the device API is called with new token
    assert len(aioclient_mock.mock_calls) == 2
    assert aioclient_mock.mock_calls[0][2] == {
        CONF_CLIENT_ID: CLIENT_ID,
        CONF_CLIENT_SECRET: CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": FAKE_REFRESH_TOKEN,
    }
    assert str(aioclient_mock.mock_calls[1][1]) == DEVICES_API_URL
    assert aioclient_mock.mock_calls[1][3].get("Authorization") == (
        "Bearer server-access-token"
    )

    # Verify updated token
    assert (
        config_entry.data["token"]["access_token"]
        == SERVER_ACCESS_TOKEN["access_token"]
    )