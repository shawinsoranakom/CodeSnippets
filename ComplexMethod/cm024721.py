async def test_auth_recover_exception(
    hass: HomeAssistant,
    mock_anglian_water_authenticator: AsyncMock,
    mock_anglian_water_client: AsyncMock,
    exception_type,
    expected_error,
) -> None:
    """Test that the flow can recover from an auth exception."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    mock_anglian_water_authenticator.send_login_request.side_effect = exception_type

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}

    # Now test we can recover

    mock_anglian_water_authenticator.send_login_request.side_effect = None

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