async def test_setup_two_trackers(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    """Test set up person with two device trackers."""
    hass.set_state(CoreState.not_running)
    user_id = hass_admin_user.id
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": [DEVICE_TRACKER, DEVICE_TRACKER_2],
        }
    }
    assert await async_setup_component(hass, DOMAIN, config)

    state = hass.states.get("person.tracked_person")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) is None
    assert state.attributes.get(ATTR_LONGITUDE) is None
    assert state.attributes.get(ATTR_SOURCE) is None
    assert state.attributes.get(ATTR_USER_ID) == user_id

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    # Router tracker at home with gps_accuracy — the person entity should get
    # coordinates from the home zone (which has no gps_accuracy),not from the
    # router tracker's attributes.
    # Note: This is not a realistic test case, a router tracker would not have
    # gps_accuracy, but we want to assert that the person entity uses latitude
    # longitude and accuracy from the home zone, not from the state attributes
    # of the device tracker.
    # Router tracker at home — person gets coordinates from the home zone,
    # not from the router tracker. The router tracker has gps_accuracy=99
    # and in_zones=["zone.fake"] to verify these are NOT propagated.
    hass.states.async_set(
        DEVICE_TRACKER,
        "home",
        {
            ATTR_SOURCE_TYPE: SourceType.ROUTER,
            ATTR_GPS_ACCURACY: 99,
            ATTR_IN_ZONES: ["zone.fake"],
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "home"
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) == 32.87336
    assert state.attributes.get(ATTR_LONGITUDE) == -117.22743
    # GPS accuracy and in_zones come from the coordinates source (home zone),
    # not from the state source (router tracker).
    assert state.attributes.get(ATTR_GPS_ACCURACY) is None
    assert state.attributes.get(ATTR_IN_ZONES) == []
    assert state.attributes.get(ATTR_SOURCE) == DEVICE_TRACKER
    assert state.attributes.get(ATTR_USER_ID) == user_id
    assert state.attributes.get(ATTR_DEVICE_TRACKERS) == [
        DEVICE_TRACKER,
        DEVICE_TRACKER_2,
    ]

    hass.states.async_set(
        DEVICE_TRACKER_2,
        "not_home",
        {
            ATTR_LATITUDE: 12.123456,
            ATTR_LONGITUDE: 13.123456,
            ATTR_GPS_ACCURACY: 12,
            ATTR_IN_ZONES: ["zone.work"],
            ATTR_SOURCE_TYPE: SourceType.GPS,
        },
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        DEVICE_TRACKER, "not_home", {ATTR_SOURCE_TYPE: SourceType.ROUTER}
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "not_home"
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) == 12.123456
    assert state.attributes.get(ATTR_LONGITUDE) == 13.123456
    assert state.attributes.get(ATTR_GPS_ACCURACY) == 12
    assert state.attributes.get(ATTR_IN_ZONES) == ["zone.work"]
    assert state.attributes.get(ATTR_SOURCE) == DEVICE_TRACKER_2
    assert state.attributes.get(ATTR_USER_ID) == user_id
    assert state.attributes.get(ATTR_DEVICE_TRACKERS) == [
        DEVICE_TRACKER,
        DEVICE_TRACKER_2,
    ]

    hass.states.async_set(DEVICE_TRACKER_2, "zone1", {ATTR_SOURCE_TYPE: SourceType.GPS})
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "zone1"
    assert state.attributes.get(ATTR_SOURCE) == DEVICE_TRACKER_2

    hass.states.async_set(DEVICE_TRACKER, "home", {ATTR_SOURCE_TYPE: SourceType.ROUTER})
    await hass.async_block_till_done()
    hass.states.async_set(DEVICE_TRACKER_2, "zone2", {ATTR_SOURCE_TYPE: SourceType.GPS})
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "home"
    assert state.attributes.get(ATTR_SOURCE) == DEVICE_TRACKER