async def test_form_with_exceptions(
    hass: HomeAssistant,
    exc: Exception,
    base_error: str,
    mock_setup_entry: AsyncMock,
    mock_imgw_pib_client: AsyncMock,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_imgw_pib_client.get_hydrological_data.side_effect = exc
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION_ID: "123"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": base_error}

    mock_imgw_pib_client.get_hydrological_data.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_STATION_ID: "123"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "River Name (Station Name)"
    assert result["data"] == {CONF_STATION_ID: "123"}
    assert result["context"]["unique_id"] == "123"
    assert len(mock_setup_entry.mock_calls) == 1