async def test_load_person_storage(
    hass: HomeAssistant, hass_admin_user: MockUser, storage_setup
) -> None:
    """Test set up person from storage."""
    state = hass.states.get("person.tracked_person")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) is None
    assert state.attributes.get(ATTR_LONGITUDE) is None
    assert state.attributes.get(ATTR_SOURCE) is None
    assert state.attributes.get(ATTR_USER_ID) == hass_admin_user.id

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()
    hass.states.async_set(DEVICE_TRACKER, "home")
    await hass.async_block_till_done()

    state = hass.states.get("person.tracked_person")
    assert state.state == "home"
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) == 32.87336
    assert state.attributes.get(ATTR_LONGITUDE) == -117.22743
    assert state.attributes.get(ATTR_SOURCE) == DEVICE_TRACKER
    assert state.attributes.get(ATTR_USER_ID) == hass_admin_user.id