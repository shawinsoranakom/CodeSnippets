async def test_full_user_flow(hass: HomeAssistant, mock_setup_entry) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Media extractor"
    assert result.get("data") == {}
    assert result.get("options") == {}
    assert len(mock_setup_entry.mock_calls) == 1