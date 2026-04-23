async def test_manual_update_entity(
    hass: HomeAssistant,
    mock_request_status: AsyncMock,
) -> None:
    """Test multiple simultaneous manual update entity via service homeassistant/update_entity.

    We should only do network call once for the multiple simultaneous update entity services.
    """
    device_slug = slugify(mock_request_status.return_value["UPSNAME"])
    # Assert the initial state of sensor.ups_load.
    state = hass.states.get(f"sensor.{device_slug}_load")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "14.0"

    # Setup HASS for calling the update_entity service.
    await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})

    mock_request_status.return_value = MOCK_STATUS | {
        "LOADPCT": "15.0 Percent",
        "BCHARGE": "99.0 Percent",
    }
    # Now, we fast-forward the time to pass the debouncer cooldown, but put it
    # before the normal update interval to see if the manual update works.
    request_call_count_before = mock_request_status.call_count
    future = utcnow() + timedelta(seconds=REQUEST_REFRESH_COOLDOWN)
    async_fire_time_changed(hass, future)
    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {
            ATTR_ENTITY_ID: [
                f"sensor.{device_slug}_load",
                f"sensor.{device_slug}_battery",
            ]
        },
        blocking=True,
    )
    # Even if we requested updates for two entities, our integration should smartly
    # group the API calls to just one.
    assert mock_request_status.call_count == request_call_count_before + 1

    # The new state should be effective.
    state = hass.states.get(f"sensor.{device_slug}_load")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "15.0"