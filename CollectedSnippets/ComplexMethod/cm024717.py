async def test_reauth_exceptions(
    hass: HomeAssistant,
    exception: Exception,
    err_msg: str,
    mock_setup_entry: AsyncMock,
    mock_ayla_api: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth flow when an exception occurs."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_ayla_api.async_sign_in.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: TEST_PASSWORD2,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": err_msg}

    mock_ayla_api.async_sign_in.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: TEST_PASSWORD2,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_PASSWORD] == TEST_PASSWORD2