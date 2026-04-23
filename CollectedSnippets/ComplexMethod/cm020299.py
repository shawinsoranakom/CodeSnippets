async def test_auth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    setup_platform: PlatformSetup,
    token_expiration_time: float,
) -> None:
    """Exercise authentication library creates valid credentials."""
    # Prepare to capture credentials in API request.  Empty payloads just mean
    # no devices or structures are loaded.
    aioclient_mock.get(f"{API_URL}/enterprises/{PROJECT_ID}/structures", json={})
    aioclient_mock.get(f"{API_URL}/enterprises/{PROJECT_ID}/devices", json={})

    # Prepare to capture credentials for Subscriber
    captured_creds = None

    def async_new_subscriber(
        credentials: Credentials,
    ) -> Mock:
        """Capture credentials for tests."""
        nonlocal captured_creds
        captured_creds = credentials
        return AsyncMock()

    with patch(
        "google_nest_sdm.subscriber_client.pubsub_v1.SubscriberAsyncClient",
        side_effect=async_new_subscriber,
    ) as new_subscriber_mock:
        await setup_platform()

    # Verify API requests are made with the correct credentials
    calls = aioclient_mock.mock_calls
    assert len(calls) == 2
    (_method, _url, _data, headers) = calls[0]
    assert headers == {"Authorization": f"Bearer {FAKE_TOKEN}"}
    (_method, _url, _data, headers) = calls[1]
    assert headers == {"Authorization": f"Bearer {FAKE_TOKEN}"}

    # Verify the subscriber was created with the correct credentials
    assert len(new_subscriber_mock.mock_calls) == 1
    assert captured_creds
    creds = captured_creds
    assert creds.token == FAKE_TOKEN
    assert creds.refresh_token == FAKE_REFRESH_TOKEN
    assert int(dt_util.as_timestamp(creds.expiry)) == int(token_expiration_time)
    assert creds.valid
    assert not creds.expired
    assert creds.token_uri == OAUTH2_TOKEN
    assert creds.client_id == CLIENT_ID
    assert creds.client_secret == CLIENT_SECRET
    assert creds.scopes == SDM_SCOPES