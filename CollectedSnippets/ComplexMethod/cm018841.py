async def test_reconfigure(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_token_response: dict[str, Any],
) -> None:
    """Test reconfigure flow."""
    mock_entry = await setup_platform(hass, [])
    client = await hass_client_no_auth()

    result = await mock_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.EXTERNAL_STEP

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT,
        },
    )
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    new_token_response = mock_token_response | {
        "refresh_token": "new_refresh_token",
        "access_token": "new_access_token",
    }
    aioclient_mock.post(TOKEN_URL, json=new_token_response)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify entry data was updated
    assert mock_entry.data["auth_implementation"] == DOMAIN
    assert mock_entry.data["token"]["refresh_token"] == "new_refresh_token"
    assert mock_entry.data["token"]["access_token"] == "new_access_token"
    assert mock_entry.data["token"]["type"] == "Bearer"
    assert mock_entry.data["token"]["expires_in"] == 60
    assert "expires_at" in mock_entry.data["token"]