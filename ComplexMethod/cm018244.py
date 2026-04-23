async def test_full_station_number_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_waqi: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the station number flow."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "station_number"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "station_number"
    assert not result["errors"]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_STATION_NUMBER: 4584},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "de Jongweg, Utrecht"
    assert result["data"] == {CONF_STATION_NUMBER: 4584}
    assert list(mock_config_entry.subentries.values())[1].unique_id == "4584"