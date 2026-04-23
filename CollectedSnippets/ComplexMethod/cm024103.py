async def test_form(
    hass: HomeAssistant,
    mock_config_flow_list_vehicles: AsyncMock,
    mock_async_setup_entry: AsyncMock,
) -> None:
    """Test we get the form."""

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result1["type"] is FlowResultType.FORM
    assert not result1["errors"]

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )
    await hass.async_block_till_done()
    assert len(mock_async_setup_entry.mock_calls) == 1
    assert len(mock_config_flow_list_vehicles.mock_calls) == 1

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Tessie"
    assert result2["data"] == TEST_CONFIG