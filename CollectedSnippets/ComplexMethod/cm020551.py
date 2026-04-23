async def test_full_user_flow(
    hass: HomeAssistant,
    mock_stookwijzer: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LOCATION: {CONF_LATITUDE: 1.0, CONF_LONGITUDE: 1.1}},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Stookwijzer"
    assert result["data"] == {
        CONF_LATITUDE: 450000.123456789,
        CONF_LONGITUDE: 200000.123456789,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_stookwijzer.async_transform_coordinates.mock_calls) == 1