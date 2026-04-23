async def test_update_interval(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test correct update interval when the number of configured instances changes."""
    REMAINING_REQUESTS = 15
    HEADERS = {
        "X-RateLimit-Limit-day": "100",
        "X-RateLimit-Remaining-day": str(REMAINING_REQUESTS),
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id="123-456",
        data={
            "api_key": "foo",
            "latitude": 123,
            "longitude": 456,
            "name": "Home",
        },
    )

    aioclient_mock.get(
        API_POINT_URL,
        text=await async_load_fixture(hass, "valid_station.json", DOMAIN),
        headers=HEADERS,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    instances = 1

    assert aioclient_mock.call_count == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state is ConfigEntryState.LOADED

    update_interval = set_update_interval(instances, REMAINING_REQUESTS)
    freezer.tick(update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # call_count should increase by one because we have one instance configured
    assert aioclient_mock.call_count == 2

    # Now we add the second Airly instance
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Work",
        unique_id="66.66-111.11",
        data={
            "api_key": "foo",
            "latitude": 66.66,
            "longitude": 111.11,
            "name": "Work",
        },
    )

    aioclient_mock.get(
        "https://airapi.airly.eu/v2/measurements/point?lat=66.660000&lng=111.110000",
        text=await async_load_fixture(hass, "valid_station.json", DOMAIN),
        headers=HEADERS,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    instances = 2

    assert aioclient_mock.call_count == 3
    assert len(hass.config_entries.async_entries(DOMAIN)) == 2
    assert entry.state is ConfigEntryState.LOADED

    update_interval = set_update_interval(instances, REMAINING_REQUESTS)
    freezer.tick(update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # call_count should increase by two because we have two instances configured
    assert aioclient_mock.call_count == 5