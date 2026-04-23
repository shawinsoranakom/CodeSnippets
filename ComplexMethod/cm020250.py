async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
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
        f"{OAUTH2_AUTHORIZE}/?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
            "user_id": "600",
        },
    )
    with patch(
        "homeassistant.components.monzo.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

        assert len(mock_setup.mock_calls) == 0

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "await_approval_confirmation"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"confirm": True}
        )

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DOMAIN
    assert "result" in result
    assert result["result"].unique_id == "600"
    assert "token" in result["result"].data
    assert result["result"].data["token"]["access_token"] == "mock-access-token"
    assert result["result"].data["token"]["refresh_token"] == "mock-refresh-token"