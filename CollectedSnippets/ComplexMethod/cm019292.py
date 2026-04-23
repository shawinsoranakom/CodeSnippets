async def test_nested_group(hass: HomeAssistant) -> None:
    """Test nested light group."""
    await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": ["light.bedroom_group"],
                    "name": "Nested Group",
                    "all": "false",
                },
                {
                    "platform": DOMAIN,
                    "entities": ["light.bed_light", "light.kitchen_lights"],
                    "name": "Bedroom Group",
                    "all": "false",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("light.bedroom_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        "light.bed_light",
        "light.kitchen_lights",
    ]

    state = hass.states.get("light.nested_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ENTITY_ID) == ["light.bedroom_group"]

    # Test controlling the nested group
    async with asyncio.timeout(0.5):
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TOGGLE,
            {ATTR_ENTITY_ID: "light.nested_group"},
            blocking=True,
        )
    assert hass.states.get("light.bed_light").state == STATE_OFF
    assert hass.states.get("light.kitchen_lights").state == STATE_OFF
    assert hass.states.get("light.bedroom_group").state == STATE_OFF
    assert hass.states.get("light.nested_group").state == STATE_OFF