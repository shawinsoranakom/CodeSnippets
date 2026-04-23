async def test_restore_home_state(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    """Test that the state is restored for a person on startup."""
    user_id = hass_admin_user.id
    attrs = {
        ATTR_ID: "1234",
        ATTR_LATITUDE: 10.12346,
        ATTR_LONGITUDE: 11.12346,
        ATTR_SOURCE: DEVICE_TRACKER,
        ATTR_USER_ID: user_id,
    }
    state = State("person.tracked_person", "home", attrs)
    mock_restore_cache(hass, (state,))
    hass.set_state(CoreState.not_running)
    mock_component(hass, "recorder")
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "tracked person",
            "user_id": user_id,
            "device_trackers": DEVICE_TRACKER,
            "picture": "/bla",
        }
    }
    assert await async_setup_component(hass, DOMAIN, config)

    state = hass.states.get("person.tracked_person")
    assert state.state == "home"
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) == 10.12346
    assert state.attributes.get(ATTR_LONGITUDE) == 11.12346
    # When restoring state the entity_id of the person will be used as source.
    assert state.attributes.get(ATTR_SOURCE) == "person.tracked_person"
    assert state.attributes.get(ATTR_USER_ID) == user_id
    assert state.attributes.get(ATTR_ENTITY_PICTURE) == "/bla"