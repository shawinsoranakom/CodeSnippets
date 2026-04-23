async def test_multiple_metering_points(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test using the config flow with multiple metering points."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "elvia.meter_value.MeterValue.get_meter_values",
        return_value={
            "meteringpoints": [
                {"meteringPointId": "1234"},
                {"meteringPointId": "5678"},
            ]
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_TOKEN: TEST_API_TOKEN,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_meter"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_METERING_POINT_ID: "5678",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "5678"
    assert result["data"] == {
        CONF_API_TOKEN: TEST_API_TOKEN,
        CONF_METERING_POINT_ID: "5678",
    }
    assert len(mock_setup_entry.mock_calls) == 1