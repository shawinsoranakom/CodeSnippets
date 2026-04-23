async def test_full_user_flow(
    hass: HomeAssistant,
    mock_cpuinfo_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "CPU Speed"
    assert result2.get("data") == {}

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_cpuinfo_config_flow.mock_calls) == 1