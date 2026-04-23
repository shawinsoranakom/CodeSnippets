async def test_reconfigure_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_namecheap: AsyncMock,
    side_effect: Exception | bool,
    text_error: str,
) -> None:
    """Test we handle errors."""

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_namecheap.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    mock_namecheap.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    assert config_entry.data[CONF_PASSWORD] == "new-password"