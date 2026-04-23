async def test_forecast_service(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
    mock_simple_nws,
    no_sensor,
    service: str,
) -> None:
    """Test multiple forecast."""
    instance = mock_simple_nws.return_value

    entry = MockConfigEntry(
        domain=nws.DOMAIN,
        data=NWS_CONFIG,
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    instance.update_observation.assert_called_once()
    instance.update_forecast.assert_called_once()
    instance.update_forecast_hourly.assert_called_once()

    for forecast_type in ("twice_daily", "hourly"):
        response = await hass.services.async_call(
            WEATHER_DOMAIN,
            service,
            {
                "entity_id": "weather.nws_35_75_abc",
                "type": forecast_type,
            },
            blocking=True,
            return_response=True,
        )
        assert response == snapshot

    # Calling the services should use cached data
    instance.update_observation.assert_called_once()
    instance.update_forecast.assert_called_once()
    instance.update_forecast_hourly.assert_called_once()

    # Trigger data refetch
    freezer.tick(nws.DEFAULT_SCAN_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert instance.update_observation.call_count == 2
    assert instance.update_forecast.call_count == 2
    assert instance.update_forecast_hourly.call_count == 2

    for forecast_type in ("twice_daily", "hourly"):
        response = await hass.services.async_call(
            WEATHER_DOMAIN,
            service,
            {
                "entity_id": "weather.nws_35_75_abc",
                "type": forecast_type,
            },
            blocking=True,
            return_response=True,
        )
        assert response == snapshot

    # Calling the services should update the hourly forecast
    assert instance.update_observation.call_count == 2
    assert instance.update_forecast.call_count == 2
    assert instance.update_forecast_hourly.call_count == 2

    # third update fails, but data is cached
    instance.update_forecast_hourly.side_effect = aiohttp.ClientError
    freezer.tick(nws.DEFAULT_SCAN_INTERVAL + timedelta(seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        service,
        {
            "entity_id": "weather.nws_35_75_abc",
            "type": "hourly",
        },
        blocking=True,
        return_response=True,
    )
    assert response == snapshot

    # after additional 35 minutes data caching expires, data is no longer shown
    freezer.tick(timedelta(minutes=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        service,
        {
            "entity_id": "weather.nws_35_75_abc",
            "type": "hourly",
        },
        blocking=True,
        return_response=True,
    )
    assert response == snapshot