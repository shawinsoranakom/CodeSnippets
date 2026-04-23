async def test_flow_reconfigure_init_data_unknown_error_and_recover_on_step_1(
    hass: HomeAssistant,
    cookidoo_config_entry: AsyncMock,
    mock_cookidoo_client: AsyncMock,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test unknown errors."""
    mock_cookidoo_client.login.side_effect = raise_error

    cookidoo_config_entry.add_to_hass(hass)
    await setup_integration(hass, cookidoo_config_entry)

    result = await cookidoo_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["handler"] == "cookidoo"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**MOCK_DATA_USER_STEP, CONF_COUNTRY: "DE"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == text_error

    # Recover
    mock_cookidoo_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={**MOCK_DATA_USER_STEP, CONF_COUNTRY: "DE"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "language"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LANGUAGE: "de-DE"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert cookidoo_config_entry.data == {
        **MOCK_DATA_USER_STEP,
        CONF_COUNTRY: "DE",
        CONF_LANGUAGE: "de-DE",
    }
    assert len(hass.config_entries.async_entries()) == 1