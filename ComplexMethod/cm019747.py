async def test_full_flow_with_domain_registration(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    access_token: str,
    mock_private_key,
) -> None:
    """Test full flow with domain registration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.EXTERNAL_STEP

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT,
        },
    )

    assert result["url"].startswith(AUTHORIZE_URL)
    parsed_url = urlparse(result["url"])
    parsed_query = parse_qs(parsed_url.query)
    assert parsed_query["response_type"][0] == "code"
    assert parsed_query["client_id"][0] == "user_client_id"
    assert parsed_query["redirect_uri"][0] == REDIRECT
    assert parsed_query["state"][0] == state
    assert parsed_query["prompt_missing_scopes"][0] == "true"
    assert parsed_query["scope"][0] == " ".join(SCOPES)
    assert "code_challenge" not in parsed_query

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": access_token,
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with (
        patch(
            "homeassistant.components.tesla_fleet.config_flow.TeslaFleetApi"
        ) as mock_api_class,
        patch(
            "homeassistant.components.tesla_fleet.async_setup_entry", return_value=True
        ),
    ):
        mock_api = AsyncMock()
        mock_api.private_key = mock_private_key
        mock_api.get_private_key = AsyncMock()
        mock_api.partner_login = AsyncMock()
        mock_api.public_uncompressed_point = "0404112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff1122"
        mock_api.partner.register.return_value = {
            "response": {
                "public_key": "0404112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff1122"
            }
        }
        mock_api_class.return_value = mock_api

        # Complete OAuth
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "domain_input"

        # Enter domain - this should automatically register and go to registration_complete
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DOMAIN: "example.com"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "registration_complete"

        # Complete flow - provide user input to complete registration
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == UNIQUE_ID
    assert result["result"].unique_id == UNIQUE_ID