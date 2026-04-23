async def test_reauth_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry,
    mock_dropbox_client,
    mock_setup_entry: AsyncMock,
    new_account_info: SimpleNamespace,
    expected_reason: str,
    expected_setup_calls: int,
    expected_access_token: str,
) -> None:
    """Test reauthentication flow outcomes."""

    mock_config_entry.add_to_hass(hass)

    mock_dropbox_client.get_account_info.return_value = new_account_info

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

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

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "token_type": "Bearer",
            "expires_in": 120,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == expected_reason
    assert mock_setup_entry.await_count == expected_setup_calls

    assert mock_config_entry.data["token"]["access_token"] == expected_access_token