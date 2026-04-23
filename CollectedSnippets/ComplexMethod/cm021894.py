async def test_full_flow(
    hass: HomeAssistant,
    mock_essent_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Essent"
    assert result["data"] == {}
    assert len(mock_setup_entry.mock_calls) == 1