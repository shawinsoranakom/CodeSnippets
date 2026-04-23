async def test_full_flow(
    hass: HomeAssistant, mock_airthings_token: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the full flow working."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_DATA,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Airthings"
    assert result["data"] == TEST_DATA
    assert result["result"].unique_id == "client_id"
    assert len(mock_setup_entry.mock_calls) == 1