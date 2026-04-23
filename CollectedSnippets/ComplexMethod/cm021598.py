async def test_setup_tracker(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    """Test set up person with one device tracker."""
    hass.set_state(CoreState.not_running)
    user_id = hass_admin_user.id
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": DEVICE_TRACKER,
        }
    }
    assert await async_setup_component(hass, DOMAIN, config)

    expected_attributes = {
        ATTR_DEVICE_TRACKERS: [DEVICE_TRACKER],
        ATTR_EDITABLE: False,
        ATTR_FRIENDLY_NAME: "tracked person",
        ATTR_ID: "1234",
        ATTR_IN_ZONES: [],
        ATTR_USER_ID: user_id,
    }

    state = hass.states.get("person.tracked_person")
    assert state.state == STATE_UNKNOWN
    assert state.attributes == expected_attributes

    # Test home without coordinates
    hass.states.async_set(DEVICE_TRACKER, "home")
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == STATE_UNKNOWN

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "home"
    assert state.attributes == expected_attributes | {
        ATTR_LATITUDE: 32.87336,
        ATTR_LONGITUDE: -117.22743,
        ATTR_SOURCE: DEVICE_TRACKER,
    }

    # Test home with coordinates
    hass.states.async_set(
        DEVICE_TRACKER,
        "home",
        {ATTR_LATITUDE: 10.123456, ATTR_LONGITUDE: 11.123456, ATTR_GPS_ACCURACY: 10},
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "home"
    assert state.attributes == expected_attributes | {
        ATTR_GPS_ACCURACY: 10,
        ATTR_LATITUDE: 10.123456,
        ATTR_LONGITUDE: 11.123456,
        ATTR_SOURCE: DEVICE_TRACKER,
    }

    # Test not_home without coordinates
    hass.states.async_set(
        DEVICE_TRACKER,
        "not_home",
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "not_home"
    assert state.attributes == expected_attributes | {ATTR_SOURCE: DEVICE_TRACKER}

    # Test not_home with coordinates
    hass.states.async_set(
        DEVICE_TRACKER,
        "not_home",
        {ATTR_LATITUDE: 10.123456, ATTR_LONGITUDE: 11.123456, ATTR_GPS_ACCURACY: 10},
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "not_home"
    assert state.attributes == expected_attributes | {
        ATTR_GPS_ACCURACY: 10,
        ATTR_LATITUDE: 10.123456,
        ATTR_LONGITUDE: 11.123456,
        ATTR_SOURCE: DEVICE_TRACKER,
    }