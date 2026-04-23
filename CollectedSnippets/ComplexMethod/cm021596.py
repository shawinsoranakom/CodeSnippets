async def test_setup_user_id(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    """Test config with user id."""
    user_id = hass_admin_user.id
    config = {DOMAIN: {"id": "1234", "name": "test person", "user_id": user_id}}
    assert await async_setup_component(hass, DOMAIN, config)

    state = hass.states.get("person.test_person")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) is None
    assert state.attributes.get(ATTR_LONGITUDE) is None
    assert state.attributes.get(ATTR_SOURCE) is None
    assert state.attributes.get(ATTR_USER_ID) == user_id