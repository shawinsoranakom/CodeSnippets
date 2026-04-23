async def test_full_flow_implementation(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test registering an integration and finishing flow works."""
    await setup_component(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pick_implementation"

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"implementation": "eneco"}
    )

    assert result2["type"] is FlowResultType.EXTERNAL_STEP
    assert result2["url"] == (
        "https://api.toon.eu/authorize"
        "?response_type=code&client_id=client"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&tenant_id=eneco&issuer=identity.toon.eu"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == HTTPStatus.OK
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        "https://api.toon.eu/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch("toonapi.Toon.agreements", return_value=[Agreement(agreement_id=123)]):
        result3 = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result3["data"]["auth_implementation"] == "eneco"
    assert result3["data"]["agreement_id"] == 123
    result3["data"]["token"].pop("expires_at")
    assert result3["data"]["token"] == {
        "refresh_token": "mock-refresh-token",
        "access_token": "mock-access-token",
        "type": "Bearer",
        "expires_in": 60,
    }