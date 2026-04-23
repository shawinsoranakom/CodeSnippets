async def test_setup_router_ble_trackers(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    """Test router and BLE trackers."""
    # BLE trackers are considered stationary trackers; however unlike a router based tracker
    # whose states are home and not_home, a BLE tracker may have the value of any zone that the
    # beacon is configured for.
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
    hass.states.async_set(
        DEVICE_TRACKER, "not_home", {ATTR_SOURCE_TYPE: SourceType.ROUTER}
    )
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "not_home"
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) is None
    assert state.attributes.get(ATTR_LONGITUDE) is None
    assert state.attributes.get(ATTR_GPS_ACCURACY) is None
    assert state.attributes.get(ATTR_SOURCE) == DEVICE_TRACKER
    assert state.attributes.get(ATTR_USER_ID) == user_id
    assert state.attributes.get(ATTR_DEVICE_TRACKERS) == [
        DEVICE_TRACKER,
        DEVICE_TRACKER_2,
    ]

    # Set the BLE tracker to the "office" zone.
    hass.states.async_set(
        DEVICE_TRACKER_2,
        "office",
        {
            ATTR_LATITUDE: 12.123456,
            ATTR_LONGITUDE: 13.123456,
            ATTR_GPS_ACCURACY: 12,
            ATTR_IN_ZONES: ["zone.office"],
            ATTR_SOURCE_TYPE: SourceType.BLUETOOTH_LE,
        },
    )
    await hass.async_block_till_done()

    # The person should be in the office.
    state = hass.states.get("person.tracked_person")
    assert state.state == "office"
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) == 12.123456
    assert state.attributes.get(ATTR_LONGITUDE) == 13.123456
    assert state.attributes.get(ATTR_GPS_ACCURACY) == 12
    assert state.attributes.get(ATTR_IN_ZONES) == ["zone.office"]
    assert state.attributes.get(ATTR_SOURCE) == DEVICE_TRACKER_2
    assert state.attributes.get(ATTR_USER_ID) == user_id
    assert state.attributes.get(ATTR_DEVICE_TRACKERS) == [
        DEVICE_TRACKER,
        DEVICE_TRACKER_2,
    ]