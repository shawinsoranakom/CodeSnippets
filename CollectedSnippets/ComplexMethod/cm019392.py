async def test_availability(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Ensure that we mark the entities unavailable correctly when service is offline."""
    await init_integration(hass, aioclient_mock)

    state = hass.states.get("sensor.home_humidity")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "68.35"

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        API_POINT_URL, exc=AirlyError(HTTPStatus.NOT_FOUND, {"message": "Not found"})
    )
    future = utcnow() + timedelta(minutes=60)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.home_humidity")
    assert state
    assert state.state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    aioclient_mock.get(
        API_POINT_URL, text=await async_load_fixture(hass, "valid_station.json", DOMAIN)
    )
    future = utcnow() + timedelta(minutes=120)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.home_humidity")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "68.35"