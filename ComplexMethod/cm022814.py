async def test_service_calls(hass: HomeAssistant) -> None:
    """Test service calls to cover."""
    await async_setup_component(hass, "switch", {"switch": [{"platform": "demo"}]})
    await hass.async_block_till_done()
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.decorative_lights",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: Platform.COVER,
        },
        title="Title is ignored",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("cover.decorative_lights").state == CoverState.OPEN

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_TOGGLE,
        {CONF_ENTITY_ID: "cover.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("cover.decorative_lights").state == CoverState.CLOSED

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {CONF_ENTITY_ID: "cover.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_ON
    assert hass.states.get("cover.decorative_lights").state == CoverState.OPEN

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {CONF_ENTITY_ID: "cover.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("cover.decorative_lights").state == CoverState.CLOSED

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {CONF_ENTITY_ID: "switch.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_ON
    assert hass.states.get("cover.decorative_lights").state == CoverState.OPEN

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {CONF_ENTITY_ID: "switch.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("cover.decorative_lights").state == CoverState.CLOSED

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TOGGLE,
        {CONF_ENTITY_ID: "switch.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_ON
    assert hass.states.get("cover.decorative_lights").state == CoverState.OPEN