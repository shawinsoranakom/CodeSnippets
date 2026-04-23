async def test_domain_input_invalid_domain(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    access_token: str,
    mock_private_key,
) -> None:
    """Test domain input with invalid domain."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT,
        },
    )

    client = await hass_client_no_auth()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

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
    ):
        mock_api = AsyncMock()
        mock_api.private_key = mock_private_key
        mock_api.get_private_key = AsyncMock()
        mock_api.partner_login = AsyncMock()
        mock_api_class.return_value = mock_api

        # Complete OAuth
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "domain_input"

        # Enter invalid domain
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DOMAIN: "invalid-domain"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "domain_input"
        assert result["errors"] == {CONF_DOMAIN: "invalid_domain"}

        # Enter valid domain - this should automatically register and go to registration_complete
        mock_api.public_uncompressed_point = "0404112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff1122"
        mock_api.partner.register.return_value = {
            "response": {
                "public_key": "0404112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff112233445566778899aabbccddeeff1122"
            }
        }
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_DOMAIN: "example.com"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "registration_complete"