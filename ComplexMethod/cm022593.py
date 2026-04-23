async def test_form(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_liebherr_client: MagicMock,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert result.get("errors") == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Liebherr"
    assert result.get("data") == MOCK_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1