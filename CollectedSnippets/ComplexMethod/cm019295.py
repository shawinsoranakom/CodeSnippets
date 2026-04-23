async def test_service_calls(hass: HomeAssistant) -> None:
    """Test service calls."""
    await async_setup_component(
        hass,
        SWITCH_DOMAIN,
        {
            SWITCH_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": [
                        "switch.ac",
                        "switch.decorative_lights",
                    ],
                    "all": "false",
                },
            ]
        },
    )
    await hass.async_block_till_done()

    group_state = hass.states.get("switch.switch_group")
    assert group_state.state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: "switch.switch_group"},
        blocking=True,
    )
    assert hass.states.get("switch.ac").state == STATE_OFF
    assert hass.states.get("switch.decorative_lights").state == STATE_OFF

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.switch_group"},
        blocking=True,
    )

    assert hass.states.get("switch.ac").state == STATE_ON
    assert hass.states.get("switch.decorative_lights").state == STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.switch_group"},
        blocking=True,
    )

    assert hass.states.get("switch.ac").state == STATE_OFF
    assert hass.states.get("switch.decorative_lights").state == STATE_OFF