async def test_user_flow_success(
    hass: HomeAssistant, mock_waterfurnace_client: Mock, mock_setup_entry: AsyncMock
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_password"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "WaterFurnace test_user"
    assert result["data"] == {
        CONF_USERNAME: "test_user",
        CONF_PASSWORD: "test_password",
    }
    assert result["result"].unique_id == "test_account_id"

    # Verify login was called (once during config flow, once during setup)
    assert mock_waterfurnace_client.login.called