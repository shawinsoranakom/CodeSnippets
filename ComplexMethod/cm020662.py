async def test_sensor_empty_response(
    hass: HomeAssistant,
    load_int: ConfigEntry,
    load_json: list[dict[str, Any]],
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the Nord Pool sensor with empty response."""

    responses = list(load_json)

    current_price = hass.states.get("sensor.nord_pool_se3_current_price")
    last_price = hass.states.get("sensor.nord_pool_se3_previous_price")
    next_price = hass.states.get("sensor.nord_pool_se3_next_price")
    assert current_price is not None
    assert last_price is not None
    assert next_price is not None
    assert current_price.state == "0.67405"
    assert last_price.state == "0.60774"
    assert next_price.state == "0.63858"

    aioclient_mock.clear_requests()
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-09-30",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=responses[1],
    )
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-01",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=responses[0],
    )
    # Future date without data should return 204
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-02",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        status=HTTPStatus.NO_CONTENT,
    )

    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # All prices should be known as tomorrow is not loaded by sensors

    current_price = hass.states.get("sensor.nord_pool_se3_current_price")
    last_price = hass.states.get("sensor.nord_pool_se3_previous_price")
    next_price = hass.states.get("sensor.nord_pool_se3_next_price")
    assert current_price is not None
    assert last_price is not None
    assert next_price is not None
    assert current_price.state == "0.63736"
    assert last_price.state == "0.63482"
    assert next_price.state == "0.66068"

    aioclient_mock.clear_requests()
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-09-30",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=responses[1],
    )
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-01",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=responses[0],
    )
    # Future date without data should return 204
    aioclient_mock.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-02",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        status=HTTPStatus.NO_CONTENT,
    )

    freezer.move_to("2025-10-01T21:45:01+00:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Current and last price should be known, next price should be unknown
    # as api responds with empty data (204)

    current_price = hass.states.get("sensor.nord_pool_se3_current_price")
    last_price = hass.states.get("sensor.nord_pool_se3_previous_price")
    next_price = hass.states.get("sensor.nord_pool_se3_next_price")
    assert current_price is not None
    assert last_price is not None
    assert next_price is not None
    assert current_price.state == "0.78568"
    assert last_price.state == "0.82005"
    assert next_price.state == STATE_UNKNOWN