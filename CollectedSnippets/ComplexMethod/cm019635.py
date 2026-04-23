async def test_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    step1_config: dict[str, Any],
    step_id: str,
    step2_config: dict[str, str],
    data_config: dict[str, str],
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=None
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        step1_config.copy(),
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == step_id
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        step2_config.copy(),
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "test-instance"
    assert result3["data"] == data_config
    mock_setup_entry.assert_called_once()