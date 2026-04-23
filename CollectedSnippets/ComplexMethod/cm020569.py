async def test_flow_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    access_token,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)

    # Start reauth flow
    result = await mock_config_entry.start_reauth_flow(hass)

    # Should show reauth confirm form
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Confirm reauth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    # Should now go to user step (OAuth)
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "new-refresh-token",
            "access_token": access_token,
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    # Verify the entry was updated, not a new one created
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1