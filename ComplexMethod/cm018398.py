async def test_fetching_data(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_opendata_client: AsyncMock,
    swiss_public_transport_config_entry: MockConfigEntry,
    raise_error: Exception,
) -> None:
    """Test fetching data."""
    await setup_integration(hass, swiss_public_transport_config_entry)

    assert swiss_public_transport_config_entry.state is ConfigEntryState.LOADED

    mock_opendata_client.async_get_data.assert_called()

    assert mock_opendata_client.async_get_data.call_count == 2

    assert len(hass.states.async_all(SENSOR_DOMAIN)) == 8

    assert (
        hass.states.get("sensor.zurich_bern_departure").state
        == "2024-01-06T17:03:00+00:00"
    )
    assert (
        hass.states.get("sensor.zurich_bern_departure_1").state
        == "2024-01-06T17:04:00+00:00"
    )
    assert (
        hass.states.get("sensor.zurich_bern_departure_2").state
        == "2024-01-06T17:05:00+00:00"
    )
    assert (
        round(float(hass.states.get("sensor.zurich_bern_trip_duration").state), 3)
        == 0.003
    )
    assert hass.states.get("sensor.zurich_bern_platform").state == "0"
    assert hass.states.get("sensor.zurich_bern_transfers").state == "0"
    assert hass.states.get("sensor.zurich_bern_delay").state == "0"
    assert hass.states.get("sensor.zurich_bern_line").state == "T10"

    # Set new data and verify it
    mock_opendata_client.connections = json.loads(
        await async_load_fixture(hass, "connections.json", DOMAIN)
    )[3:6]
    freezer.tick(DEFAULT_UPDATE_TIME)
    async_fire_time_changed(hass)
    assert mock_opendata_client.async_get_data.call_count == 3
    assert (
        hass.states.get("sensor.zurich_bern_departure").state
        == "2024-01-06T17:06:00+00:00"
    )

    # Simulate fetch exception
    mock_opendata_client.async_get_data.side_effect = raise_error
    freezer.tick(DEFAULT_UPDATE_TIME)
    async_fire_time_changed(hass)
    assert mock_opendata_client.async_get_data.call_count == 4
    assert hass.states.get("sensor.zurich_bern_departure").state == "unavailable"

    # Recover and fetch new data again
    mock_opendata_client.async_get_data.side_effect = None
    mock_opendata_client.connections = json.loads(
        await async_load_fixture(hass, "connections.json", DOMAIN)
    )[6:9]
    freezer.tick(DEFAULT_UPDATE_TIME)
    async_fire_time_changed(hass)
    assert mock_opendata_client.async_get_data.call_count == 5
    assert (
        hass.states.get("sensor.zurich_bern_departure").state
        == "2024-01-06T17:09:00+00:00"
    )