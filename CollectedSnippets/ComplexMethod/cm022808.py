async def test_light_service_calls_inverted(hass: HomeAssistant) -> None:
    """Test service calls to light."""
    await async_setup_component(hass, "switch", {"switch": [{"platform": "demo"}]})
    await hass.async_block_till_done()
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.decorative_lights",
            CONF_INVERT: True,
            CONF_TARGET_DOMAIN: Platform.LIGHT,
        },
        title="decorative_lights",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("light.decorative_lights").state == STATE_ON

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TOGGLE,
        {CONF_ENTITY_ID: "light.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("light.decorative_lights").state == STATE_OFF

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {CONF_ENTITY_ID: "light.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_ON
    assert hass.states.get("light.decorative_lights").state == STATE_ON
    assert (
        hass.states.get("light.decorative_lights").attributes.get(ATTR_COLOR_MODE)
        == ColorMode.ONOFF
    )

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {CONF_ENTITY_ID: "light.decorative_lights"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("light.decorative_lights").state == STATE_OFF