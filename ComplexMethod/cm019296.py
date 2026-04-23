async def test_nested_group(hass: HomeAssistant) -> None:
    """Test nested switch group."""
    await async_setup_component(
        hass,
        SWITCH_DOMAIN,
        {
            SWITCH_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": ["switch.some_group"],
                    "name": "Nested Group",
                    "all": "false",
                },
                {
                    "platform": DOMAIN,
                    "entities": ["switch.ac", "switch.decorative_lights"],
                    "name": "Some Group",
                    "all": "false",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("switch.some_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        "switch.ac",
        "switch.decorative_lights",
    ]

    state = hass.states.get("switch.nested_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ENTITY_ID) == ["switch.some_group"]

    # Test controlling the nested group
    async with asyncio.timeout(0.5):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TOGGLE,
            {ATTR_ENTITY_ID: "switch.nested_group"},
            blocking=True,
        )
    assert hass.states.get("switch.ac").state == STATE_OFF
    assert hass.states.get("switch.decorative_lights").state == STATE_OFF
    assert hass.states.get("switch.some_group").state == STATE_OFF
    assert hass.states.get("switch.nested_group").state == STATE_OFF