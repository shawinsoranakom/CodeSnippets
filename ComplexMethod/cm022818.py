async def test_service_calls(hass: HomeAssistant) -> None:
    """Test service calls affecting the switch as lock entity."""
    await async_setup_component(hass, "switch", {"switch": [{"platform": "demo"}]})
    await hass.async_block_till_done()
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.decorative_lights",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: Platform.LOCK,
        },
        title="Title is ignored",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("lock.decorative_lights").state == LockState.UNLOCKED

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {CONF_ENTITY_ID: "lock.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("lock.decorative_lights").state == LockState.LOCKED

    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_UNLOCK,
        {CONF_ENTITY_ID: "lock.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_ON
    assert hass.states.get("lock.decorative_lights").state == LockState.UNLOCKED

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {CONF_ENTITY_ID: "switch.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("lock.decorative_lights").state == LockState.LOCKED

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {CONF_ENTITY_ID: "switch.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_ON
    assert hass.states.get("lock.decorative_lights").state == LockState.UNLOCKED

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TOGGLE,
        {CONF_ENTITY_ID: "switch.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("lock.decorative_lights").state == LockState.LOCKED