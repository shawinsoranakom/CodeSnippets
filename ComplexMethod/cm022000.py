async def test_form_user(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_panel: AsyncMock,
    panel_model: PanelModel,
    serial_number: str,
    config_flow_data: dict[str, Any],
) -> None:
    """Test the config flow for bosch_alarm."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
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
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Bosch {panel_model.name}"
    assert (
        result["data"]
        == {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 7700,
            CONF_MODEL: panel_model.name,
        }
        | config_flow_data
    )
    assert result["result"].unique_id == serial_number
    assert len(mock_setup_entry.mock_calls) == 1