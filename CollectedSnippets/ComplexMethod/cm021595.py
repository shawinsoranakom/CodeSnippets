async def test_minimal_setup(hass: HomeAssistant) -> None:
    """Test minimal config with only name."""
    config = {DOMAIN: {"id": "1234", "name": "test person"}}
    assert await async_setup_component(hass, DOMAIN, config)

    state = hass.states.get("person.test_person")
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get(ATTR_LATITUDE) is None
    assert state.attributes.get(ATTR_LONGITUDE) is None
    assert state.attributes.get(ATTR_SOURCE) is None
    assert state.attributes.get(ATTR_USER_ID) is None
    assert state.attributes.get(ATTR_ENTITY_PICTURE) is None