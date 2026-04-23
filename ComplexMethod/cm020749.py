async def test_legacy_migration_no_email_in_jwt(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_legacy_config_entry: MockConfigEntry,
    jwt: str,  # JWT with empty email array
) -> None:
    """Test migration from legacy config succeeds when JWT has no email (can't validate)."""

    mock_legacy_config_entry.add_to_hass(hass)

    # Start reauth flow
    mock_legacy_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "auth"

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
            "access_token": jwt,  # JWT with email: []
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "user_id": USER_ID,
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    # Verify the entry was updated (allowed because no email to validate)
    assert mock_legacy_config_entry.unique_id == USER_ID  # Updated from email to userId
    assert "token" in mock_legacy_config_entry.data
    assert mock_legacy_config_entry.data["auth_implementation"] == "august"
    assert mock_legacy_config_entry.data["token"]["access_token"] == jwt