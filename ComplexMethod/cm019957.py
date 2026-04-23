async def test_reconfigure_not_successful(
    hass: HomeAssistant,
    exc: Exception,
    base_error: str,
    mock_brother_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test starting a reconfigure flow but no connection found."""
    await init_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_brother_client.async_update.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": base_error}

    mock_brother_client.async_update.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.10.10.10",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        CONF_HOST: "10.10.10.10",
        CONF_TYPE: "laser",
        SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
    }