async def test_oauth_session_no_token_refresh_needed(
    hass: HomeAssistant,
    flow_handler: type[config_entry_oauth2_flow.AbstractOAuth2FlowHandler],
    local_impl: config_entry_oauth2_flow.LocalOAuth2Implementation,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the OAuth2 session helper when no refresh is needed."""
    flow_handler.async_register_implementation(hass, local_impl)

    aioclient_mock.post("https://example.com", status=201)

    config_entry = MockConfigEntry(
        domain=TEST_DOMAIN,
        data={
            "auth_implementation": TEST_DOMAIN,
            "token": {
                "refresh_token": REFRESH_TOKEN,
                "access_token": ACCESS_TOKEN_1,
                "expires_in": 500,
                "expires_at": time.time() + 500,  # Should NOT refresh
                "token_type": "bearer",
                "random_other_data": "should_stay",
            },
        },
    )

    now = time.time()
    session = config_entry_oauth2_flow.OAuth2Session(hass, config_entry, local_impl)
    resp = await session.async_request("post", "https://example.com")
    assert resp.status == 201

    # make request (no refresh)
    assert len(aioclient_mock.mock_calls) == 1

    assert (
        aioclient_mock.mock_calls[0][3]["authorization"] == f"Bearer {ACCESS_TOKEN_1}"
    )

    assert config_entry.data["token"]["refresh_token"] == REFRESH_TOKEN
    assert config_entry.data["token"]["access_token"] == ACCESS_TOKEN_1
    assert config_entry.data["token"]["expires_in"] == 500
    assert config_entry.data["token"]["random_other_data"] == "should_stay"
    assert round(config_entry.data["token"]["expires_at"] - now) == 500