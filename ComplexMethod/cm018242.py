async def test_map_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_waqi: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error: str,
) -> None:
    """Test we get the form."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "station"),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"next_step_id": "map"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "map"
    assert not result["errors"]

    mock_waqi.get_by_coordinates.side_effect = exception

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            ATTR_LOCATION: {ATTR_LATITUDE: 50.0, ATTR_LONGITUDE: 10.0},
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "map"
    assert result["errors"] == {"base": error}

    mock_waqi.get_by_coordinates.side_effect = None

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            ATTR_LOCATION: {ATTR_LATITUDE: 50.0, ATTR_LONGITUDE: 10.0},
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY