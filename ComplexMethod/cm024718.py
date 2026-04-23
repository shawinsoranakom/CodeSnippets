async def test_multiple_account_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_anglian_water_authenticator: AsyncMock,
    mock_anglian_water_client: AsyncMock,
) -> None:
    """Test the config flow when there are multiple accounts."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_account"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ACCOUNT_NUMBER
    assert result["data"][CONF_USERNAME] == USERNAME
    assert result["data"][CONF_PASSWORD] == PASSWORD
    assert result["data"][CONF_ACCESS_TOKEN] == ACCESS_TOKEN
    assert result["data"][CONF_ACCOUNT_NUMBER] == ACCOUNT_NUMBER
    assert result["result"].unique_id == ACCOUNT_NUMBER