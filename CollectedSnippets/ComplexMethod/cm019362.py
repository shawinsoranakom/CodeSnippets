async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the full OAuth2 config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.EXTERNAL_STEP
    assert "url" in result
    assert OAUTH2_AUTHORIZE in result.get("url", "")
    assert "response_type=code" in result.get("url", "")
    assert "scope=" in result.get("url", "")

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value="user123",
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result.get("type") is FlowResultType.CREATE_ENTRY
        assert result.get("title") == "Watts Vision +"
        assert "token" in result.get("data", {})
        assert len(hass.config_entries.async_entries(DOMAIN)) == 1

        assert hass.config_entries.async_entries(DOMAIN)[0].unique_id == "user123"