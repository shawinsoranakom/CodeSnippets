async def test_option_flow_wrong_coordinates(hass: HomeAssistant) -> None:
    """Test config flow options with mixed up coordinates."""
    valid_option = {
        "lat_ne": 32.1234567,
        "lon_ne": -117.2345678,
        "lat_sw": 32.2345678,
        "lon_sw": -117.1234567,
        "show_on_map": False,
        "area_name": "Home",
        "mode": "avg",
    }

    expected_result = {
        "lat_ne": 32.2345678,
        "lon_ne": -117.1234567,
        "lat_sw": 32.1234567,
        "lon_sw": -117.2345678,
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