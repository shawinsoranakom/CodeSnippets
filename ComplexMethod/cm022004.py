async def test_reconfig_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_panel: AsyncMock,
    panel_model: PanelModel,
    serial_number: str,
    config_flow_data: dict[str, Any],
) -> None:
    """Test reconfig auth."""
    await setup_integration(hass, mock_config_entry)

    config_flow_data = {k: f"{v}2" for k, v in config_flow_data.items()}
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_RECONFIGURE,
            "entry_id": mock_config_entry.entry_id,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "1.1.1.1", CONF_PORT: 7700},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == {}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        config_flow_data,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        CONF_HOST: "1.1.1.1",
        CONF_PORT: 7700,
        CONF_MODEL: panel_model.name,
        **config_flow_data,
    }