async def test_services(hass: HomeAssistant, calls: list[ServiceCall]) -> None:
    """Test the automation services for turning entities on/off."""
    entity_id = "automation.hello"

    assert hass.states.get(entity_id) is None
    assert not automation.is_on(hass, entity_id)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {"action": "test.automation"},
            }
        },
    )

    assert hass.states.get(entity_id) is not None
    assert automation.is_on(hass, entity_id)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 1

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: entity_id,
        },
        blocking=True,
    )

    assert not automation.is_on(hass, entity_id)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 1

    await hass.services.async_call(
        automation.DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    assert automation.is_on(hass, entity_id)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 2

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert not automation.is_on(hass, entity_id)
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    assert len(calls) == 2

    await hass.services.async_call(
        automation.DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.services.async_call(
        automation.DOMAIN, SERVICE_TRIGGER, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert len(calls) == 3

    await hass.services.async_call(
        automation.DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    await hass.services.async_call(
        automation.DOMAIN, SERVICE_TRIGGER, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert len(calls) == 4

    await hass.services.async_call(
        automation.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    assert automation.is_on(hass, entity_id)