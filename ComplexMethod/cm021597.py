async def test_valid_invalid_user_ids(
    hass: HomeAssistant, hass_admin_user: MockUser
) -> None:
    """Test a person with valid user id and a person with invalid user id ."""
    user_id = hass_admin_user.id
    config = {
        DOMAIN: [
            {"id": "1234", "name": "test valid user", "user_id": user_id},
            {"id": "5678", "name": "test bad user", "user_id": "bad_user_id"},
        ]
    }
    assert await async_setup_component(hass, DOMAIN, config)

    state = hass.states.get("person.test_valid_user")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_ID) == "1234"
    assert state.attributes.get(ATTR_LATITUDE) is None
    assert state.attributes.get(ATTR_LONGITUDE) is None
    assert state.attributes.get(ATTR_SOURCE) is None
    assert state.attributes.get(ATTR_USER_ID) == user_id
    state = hass.states.get("person.test_bad_user")
    assert state is None