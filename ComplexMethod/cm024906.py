async def test_abort_oauth_with_pkce_rejected(
    hass: HomeAssistant,
    flow_handler: type[config_entry_oauth2_flow.AbstractOAuth2FlowHandler],
    local_impl_pkce: config_entry_oauth2_flow.LocalOAuth2ImplementationWithPkce,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Check bad oauth token."""
    flow_handler.async_register_implementation(hass, local_impl_pkce)

    result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    code_challenge = local_impl_pkce.compute_code_challenge(MOCK_SECRET_TOKEN_URLSAFE)
    assert result["type"] == data_entry_flow.FlowResultType.EXTERNAL_STEP

    assert result["url"].startswith(f"{AUTHORIZE_URL}?")
    assert f"client_id={CLIENT_ID}" in result["url"]
    assert "redirect_uri=https://example.com/auth/external/callback" in result["url"]
    assert f"state={state}" in result["url"]
    assert "scope=read+write" in result["url"]
    assert "response_type=code" in result["url"]
    assert f"code_challenge={code_challenge}" in result["url"]
    assert "code_challenge_method=S256" in result["url"]

    client = await hass_client_no_auth()
    resp = await client.get(
        f"/auth/external/callback?error=access_denied&state={state}"
    )
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "user_rejected_authorize"
    assert result["description_placeholders"] == {"error": "access_denied"}