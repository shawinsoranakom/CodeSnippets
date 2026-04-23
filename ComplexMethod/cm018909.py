async def test_local_reauth_legacy(hass: HomeAssistant) -> None:
    """Test legacy reauthentication flow with username/password."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_GATEWAY_ID,
        version=2,
        data={
            "host": TEST_HOST,
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "verify_ssl": True,
            "hub": TEST_SERVER,
            "api_type": "local",
        },
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "local_or_cloud"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"api_type": "local"},
    )

    assert result2["step_id"] == "local"

    with patch.multiple(
        "pyoverkiz.client.OverkizClient",
        login=AsyncMock(return_value=True),
        get_gateways=AsyncMock(return_value=MOCK_GATEWAY_RESPONSE),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": TEST_HOST,
                "token": "new_token",
                "verify_ssl": True,
            },
        )

        assert result3["type"] is FlowResultType.ABORT
        assert result3["reason"] == "reauth_successful"
        assert mock_entry.data["host"] == TEST_HOST
        assert mock_entry.data["token"] == "new_token"
        assert mock_entry.data["verify_ssl"] is True