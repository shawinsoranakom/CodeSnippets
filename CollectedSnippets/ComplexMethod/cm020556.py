async def test_lights_turn_on_when_coming_home_after_sun_set_person(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test lights turn on when coming home after sun set."""
    # Ensure all setup tasks are done (avoid flaky tests)
    await hass.async_block_till_done(wait_background_tasks=True)

    device_1 = f"{DEVICE_TRACKER_DOMAIN}.device_1"
    device_2 = f"{DEVICE_TRACKER_DOMAIN}.device_2"

    test_time = datetime(2017, 4, 5, 3, 2, 3, tzinfo=dt_util.UTC)
    freezer.move_to(test_time)
    await hass.services.async_call(
        light.DOMAIN, light.SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "all"}, blocking=True
    )
    hass.states.async_set(device_1, STATE_NOT_HOME)
    hass.states.async_set(device_2, STATE_NOT_HOME)
    await hass.async_block_till_done()

    assert all(
        not light.is_on(hass, ent_id)
        for ent_id in hass.states.async_entity_ids("light")
    )
    assert hass.states.get(device_1).state == "not_home"
    assert hass.states.get(device_2).state == "not_home"

    assert await async_setup_component(
        hass,
        "person",
        {"person": [{"id": "me", "name": "Me", "device_trackers": [device_1]}]},
    )

    assert await async_setup_component(hass, "group", {})
    await hass.async_block_till_done()
    await group.Group.async_create_group(
        hass,
        "person_me",
        created_by_service=False,
        entity_ids=["person.me"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    assert await async_setup_component(
        hass,
        device_sun_light_trigger.DOMAIN,
        {device_sun_light_trigger.DOMAIN: {"device_group": "group.person_me"}},
    )

    assert all(
        hass.states.get(ent_id).state == STATE_OFF
        for ent_id in hass.states.async_entity_ids("light")
    )
    assert hass.states.get(device_1).state == "not_home"
    assert hass.states.get(device_2).state == "not_home"
    assert hass.states.get("person.me").state == "not_home"

    # Unrelated device has no impact
    hass.states.async_set(device_2, STATE_HOME)
    await hass.async_block_till_done()

    assert all(
        hass.states.get(ent_id).state == STATE_OFF
        for ent_id in hass.states.async_entity_ids("light")
    )
    assert hass.states.get(device_1).state == "not_home"
    assert hass.states.get(device_2).state == "home"
    assert hass.states.get("person.me").state == "not_home"

    # person home switches on
    hass.states.async_set(device_1, STATE_HOME)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert all(
        hass.states.get(ent_id).state == light.STATE_ON
        for ent_id in hass.states.async_entity_ids("light")
    )
    assert hass.states.get(device_1).state == "home"
    assert hass.states.get(device_2).state == "home"
    assert hass.states.get("person.me").state == "home"