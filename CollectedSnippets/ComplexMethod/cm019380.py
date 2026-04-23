async def test_option_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    valid_option = {
        "lat_ne": 32.91336,
        "lon_ne": -117.187429,
        "lat_sw": 32.83336,
        "lon_sw": -117.26743,
        "show_on_map": False,
        "area_name": "Home",
        "mode": "avg",
    }

    expected_result = {
        "lat_ne": 32.9133601,
        "lon_ne": -117.1874289,
        "lat_sw": 32.8333601,
        "lon_sw": -117.26742990000001,
        "show_on_map": False,
        "area_name": "Home",
        "mode": "avg",
    }

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data=VALID_CONFIG,
        options={},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "public_weather_areas"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_NEW_AREA: "Home"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "public_weather"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=valid_option
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "public_weather_areas"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    for k, v in expected_result.items():
        assert config_entry.options[CONF_WEATHER_AREAS]["Home"][k] == v