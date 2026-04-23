async def test_full_flow(
    hass: HomeAssistant, mock_srp_auth: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_CREDENTIALS,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "auth_implementation": "gentex_homelink",
        "token": {
            "access_token": TEST_ACCESS_JWT,
            "refresh_token": "refresh",
            "expires_in": 3600,
            "token_type": "bearer",
            "expires_at": result["data"]["token"]["expires_at"],
        },
    }
    assert result["result"].unique_id == TEST_UNIQUE_ID
    assert result["title"] == "HomeLink"