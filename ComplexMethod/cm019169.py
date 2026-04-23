async def test_dhcp_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    dhcp_discovery: DhcpServiceInfo,
) -> None:
    """Test DHCP discovery."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context=ConfigFlowContext(source=config_entries.SOURCE_DHCP),
        data=dhcp_discovery,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "oauth_discovery"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == HTTPStatus.OK
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": FAKE_REFRESH_TOKEN,
            "access_token": FAKE_ACCESS_TOKEN,
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.home_connect.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    assert hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, "1234567890")
    assert len(mock_setup_entry.mock_calls) == 1