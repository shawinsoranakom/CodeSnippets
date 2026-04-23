async def test_full_user_flow(
    hass: HomeAssistant,
    mock_garages_amsterdam: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert not result.get("errors")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"garage_name": "IJDok"},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "IJDok"
    assert result.get("data") == {"garage_name": "IJDok"}
    assert len(mock_garages_amsterdam.all_garages.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1