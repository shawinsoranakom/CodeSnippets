async def test_counter_max(hass: HomeAssistant, hass_admin_user: MockUser) -> None:
    """Test that max works."""
    assert await async_setup_component(
        hass, DOMAIN, {"counter": {"test": {"maximum": "0", "initial": "0"}}}
    )

    state = hass.states.get("counter.test")
    assert state is not None
    assert state.state == "0"

    await hass.services.async_call(
        DOMAIN,
        "increment",
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("counter.test")
    assert state2 is not None
    assert state2.state == "0"

    await hass.services.async_call(
        DOMAIN,
        "decrement",
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("counter.test")
    assert state2 is not None
    assert state2.state == "-1"