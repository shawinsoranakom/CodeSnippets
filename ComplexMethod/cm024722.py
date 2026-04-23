async def test_account_recover_exception(
    hass: HomeAssistant,
    mock_anglian_water_authenticator: AsyncMock,
    mock_anglian_water_client: AsyncMock,
    exception_type,
    expected_error,
) -> None:
    """Test that the flow can recover from an account related exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
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

    mock_anglian_water_client.validate_smart_meter.side_effect = exception_type

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_account"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_account"
    assert result["errors"] == {"base": expected_error}

    # Now test we can recover

    mock_anglian_water_client.validate_smart_meter.side_effect = None

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