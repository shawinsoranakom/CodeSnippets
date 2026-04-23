async def test_abort_if_oauth_token_closing_error(
    hass: HomeAssistant,
    flow_handler: type[config_entry_oauth2_flow.AbstractOAuth2FlowHandler],
    local_impl: config_entry_oauth2_flow.LocalOAuth2Implementation,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Check error when obtaining an oauth token."""
    flow_handler.async_register_implementation(hass, local_impl)
    config_entry_oauth2_flow.async_register_implementation(
        hass, TEST_DOMAIN, MockOAuth2Implementation()
    )

    result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "pick_implementation"

    # Pick implementation
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"implementation": TEST_DOMAIN}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.EXTERNAL_STEP
    assert result["url"] == (
        f"{AUTHORIZE_URL}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=read+write"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        TOKEN_URL,
        status=HTTPStatus.UNAUTHORIZED,
        closing=True,
    )

    with caplog.at_level(logging.DEBUG):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert "Token request for oauth2_test failed (401): unknown" in caplog.text

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "oauth_unauthorized"