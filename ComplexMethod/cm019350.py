async def test_update_error(
    hass: HomeAssistant,
    component_setup,
    mock_events_list,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test that the calendar update handles a server error."""

    now = dt_util.now()
    mock_events_list(
        {
            "items": [
                {
                    **TEST_EVENT,
                    "start": {
                        "dateTime": (now + datetime.timedelta(minutes=-30)).isoformat()
                    },
                    "end": {
                        "dateTime": (now + datetime.timedelta(minutes=30)).isoformat()
                    },
                }
            ]
        }
    )
    assert await component_setup()

    state = hass.states.get(TEST_ENTITY)
    assert state.name == TEST_ENTITY_NAME
    assert state.state == "on"

    # Advance time to next data update interval
    now += datetime.timedelta(minutes=30)

    aioclient_mock.clear_requests()
    mock_events_list({}, exc=ClientError())

    with patch("homeassistant.util.utcnow", return_value=now):
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()
        # Ensure coordinator update completes
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    # Entity is marked uanvailable due to API failure
    state = hass.states.get(TEST_ENTITY)
    assert state.name == TEST_ENTITY_NAME
    assert state.state == "unavailable"

    # Advance time past next coordinator update
    now += datetime.timedelta(minutes=30)

    aioclient_mock.clear_requests()
    mock_events_list(
        {
            "items": [
                {
                    **TEST_EVENT,
                    "start": {
                        "dateTime": (now + datetime.timedelta(minutes=30)).isoformat()
                    },
                    "end": {
                        "dateTime": (now + datetime.timedelta(minutes=60)).isoformat()
                    },
                }
            ]
        }
    )

    with patch("homeassistant.util.utcnow", return_value=now):
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()
        # Ensure coordinator update completes
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    # State updated with new API response
    state = hass.states.get(TEST_ENTITY)
    assert state.name == TEST_ENTITY_NAME
    assert state.state == "off"