async def test_light_service_calls(hass: HomeAssistant) -> None:
    """Test service calls to light."""
    await async_setup_component(hass, "switch", {"switch": [{"platform": "demo"}]})
    await async_setup_component(
        hass,
        "light",
        {"light": [{"platform": "switch", "entity_id": "switch.decorative_lights"}]},
    )
    await hass.async_block_till_done()

    assert hass.states.get("light.light_switch").state == "on"

    await common.async_toggle(hass, "light.light_switch")
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == "off"
    assert hass.states.get("light.light_switch").state == "off"

    await common.async_turn_on(hass, "light.light_switch")
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == "on"
    assert hass.states.get("light.light_switch").state == "on"
    assert (
        hass.states.get("light.light_switch").attributes.get(ATTR_COLOR_MODE)
        == ColorMode.ONOFF
    )

    await common.async_turn_off(hass, "light.light_switch")
    await hass.async_block_till_done()

    assert hass.states.get("switch.decorative_lights").state == "off"
    assert hass.states.get("light.light_switch").state == "off"