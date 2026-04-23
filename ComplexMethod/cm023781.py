async def test_reconfigure_flow_fails(
    hass: HomeAssistant, side_effect: Exception, base_error: str
) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "1234567890",
            CONF_STATION: "Vallby",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        side_effect=side_effect(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891", CONF_STATION: "Vallby_new"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": base_error}

    with (
        patch(
            "homeassistant.components.trafikverket_weatherstation.config_flow.TrafikverketWeather.async_get_weather",
        ),
        patch(
            "homeassistant.components.trafikverket_weatherstation.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "1234567891", CONF_STATION: "Vallby_new"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {"api_key": "1234567891", "station": "Vallby_new"}