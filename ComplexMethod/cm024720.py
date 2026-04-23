async def test_already_configured(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_anglian_water_authenticator: AsyncMock,
    mock_anglian_water_client: AsyncMock,
) -> None:
    """Test that the flow aborts when the entry is already added."""
    mock_config_entry.add_to_hass(hass)

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

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_account"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ACCOUNT_NUMBER: ACCOUNT_NUMBER,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"