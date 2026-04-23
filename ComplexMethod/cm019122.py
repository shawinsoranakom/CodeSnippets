async def test_token_refresh_success(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    client: MagicMock,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    config_entry: MockConfigEntry,
    platforms: list[Platform],
) -> None:
    """Test where token is expired and the refresh attempt succeeds."""

    assert config_entry.data["token"]["access_token"] == FAKE_ACCESS_TOKEN

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json=SERVER_ACCESS_TOKEN,
    )
    appliances = client.get_home_appliances.return_value

    async def mock_get_home_appliances():
        await client._auth.async_get_access_token()
        return appliances

    client.get_home_appliances.return_value = None
    client.get_home_appliances.side_effect = mock_get_home_appliances

    def init_side_effect(auth) -> MagicMock:
        client._auth = auth
        return client

    assert config_entry.state is ConfigEntryState.NOT_LOADED
    with (
        patch("homeassistant.components.home_connect.PLATFORMS", platforms),
        patch("homeassistant.components.home_connect.HomeConnectClient") as client_mock,
    ):
        client_mock.side_effect = MagicMock(side_effect=init_side_effect)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    # Verify token request
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[0][2] == {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": FAKE_REFRESH_TOKEN,
    }

    # Verify updated token
    assert (
        config_entry.data["token"]["access_token"]
        == SERVER_ACCESS_TOKEN["access_token"]
    )