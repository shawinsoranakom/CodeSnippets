async def test_public_weather_sensor(
    hass: HomeAssistant, config_entry: MockConfigEntry, netatmo_auth: AsyncMock
) -> None:
    """Test public weather sensor setup."""
    with selected_platforms([Platform.SENSOR]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    assert len(hass.states.async_all()) > 0

    prefix = "sensor.home_max_"

    assert hass.states.get(f"{prefix}temperature").state == "27.4"
    assert hass.states.get(f"{prefix}humidity").state == "76"
    assert hass.states.get(f"{prefix}atmospheric_pressure").state == "1014.4"

    prefix = "sensor.home_min_"

    assert hass.states.get(f"{prefix}temperature").state == "19.8"
    assert hass.states.get(f"{prefix}humidity").state == "56"
    assert hass.states.get(f"{prefix}atmospheric_pressure").state == "1005.4"

    prefix = "sensor.home_avg_"

    assert hass.states.get(f"{prefix}temperature").state == "22.7"
    assert hass.states.get(f"{prefix}humidity").state == "63.2"
    assert hass.states.get(f"{prefix}atmospheric_pressure").state == "1010.4"

    entities_before_change = len(hass.states.async_all())

    valid_option = {
        "lat_ne": 32.91336,
        "lon_ne": -117.187429,
        "lat_sw": 32.83336,
        "lon_sw": -117.26743,
        "show_on_map": True,
        "area_name": "Home avg",
        "mode": "max",
    }

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"new_area": "Home avg"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=valid_option
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )

    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == entities_before_change
    assert hass.states.get(f"{prefix}temperature").state == "27.4"