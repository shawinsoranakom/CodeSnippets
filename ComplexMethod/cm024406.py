async def test_state(hass: HomeAssistant) -> None:
    """Test the state of a zone."""
    info = {
        "name": "Test Zone",
        "latitude": 32.880837,
        "longitude": -117.237561,
        "radius": 250,
        "passive": False,
    }
    assert await setup.async_setup_component(hass, zone.DOMAIN, {"zone": info})

    assert len(hass.states.async_entity_ids("zone")) == 2
    state = hass.states.get("zone.test_zone")
    assert state.state == "0"
    assert state.attributes[ATTR_PERSONS] == []

    # Person entity enters zone
    hass.states.async_set(
        "person.person1",
        "Test Zone",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    assert state
    assert state.state == "1"
    assert state.attributes[ATTR_PERSONS] == ["person.person1"]

    state = hass.states.get("zone.home")
    assert state
    assert state.state == "0"
    assert state.attributes[ATTR_PERSONS] == []

    # Person entity enters zone (case insensitive)
    hass.states.async_set(
        "person.person2",
        "TEST zone",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    assert state
    assert state.state == "2"
    assert sorted(state.attributes[ATTR_PERSONS]) == [
        "person.person1",
        "person.person2",
    ]

    state = hass.states.get("zone.home")
    assert state
    assert state.state == "0"
    assert state.attributes[ATTR_PERSONS] == []

    # Person entity enters another zone
    hass.states.async_set(
        "person.person1",
        "home",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    assert state
    assert state.state == "1"
    assert state.attributes[ATTR_PERSONS] == ["person.person2"]

    state = hass.states.get("zone.home")
    assert state
    assert state.state == "1"
    assert state.attributes[ATTR_PERSONS] == ["person.person1"]

    # Person entity enters not_home
    hass.states.async_set(
        "person.person1",
        "not_home",
    )
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    assert state
    assert state.state == "1"
    assert state.attributes[ATTR_PERSONS] == ["person.person2"]

    # Person entity removed
    hass.states.async_remove("person.person2")
    await hass.async_block_till_done()

    state = hass.states.get("zone.test_zone")
    assert state
    assert state.state == "0"
    assert state.attributes[ATTR_PERSONS] == []

    state = hass.states.get("zone.home")
    assert state
    assert state.state == "0"
    assert state.attributes[ATTR_PERSONS] == []