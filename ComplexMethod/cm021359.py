async def test_get_general_forecasts(
    hass: HomeAssistant,
    general_channel_config_entry: MockConfigEntry,
) -> None:
    """Test fetching general forecasts."""
    await setup_integration(hass, general_channel_config_entry)
    result = await hass.services.async_call(
        DOMAIN,
        "get_forecasts",
        {ATTR_CONFIG_ENTRY_ID: GENERAL_ONLY_SITE_ID, ATTR_CHANNEL_TYPE: "general"},
        blocking=True,
        return_response=True,
    )
    assert len(result["forecasts"]) == 3

    first = result["forecasts"][0]
    assert first["duration"] == 30
    assert first["date"] == "2021-09-21"
    assert first["nem_date"] == "2021-09-21T09:00:00+10:00"
    assert first["per_kwh"] == 0.09
    assert first["spot_per_kwh"] == 0.01
    assert first["start_time"] == "2021-09-21T08:30:00+10:00"
    assert first["end_time"] == "2021-09-21T09:00:00+10:00"
    assert first["renewables"] == 50
    assert first["spike_status"] == "none"
    assert first["descriptor"] == "very_low"