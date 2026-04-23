async def test_nested_group(hass: HomeAssistant) -> None:
    """Test nested valve group."""
    await async_setup_component(
        hass,
        VALVE_DOMAIN,
        {
            VALVE_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": "group",
                    "entities": ["valve.bedroom_group"],
                    "name": "Nested Group",
                },
                {
                    "platform": "group",
                    CONF_ENTITIES: [DEMO_VALVE_POS1, DEMO_VALVE_POS2],
                    "name": "Bedroom Group",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("valve.bedroom_group")
    assert state is not None
    assert state.state == ValveState.OPEN
    assert state.attributes.get(ATTR_ENTITY_ID) == [DEMO_VALVE_POS1, DEMO_VALVE_POS2]

    state = hass.states.get("valve.nested_group")
    assert state is not None
    assert state.state == ValveState.OPEN
    assert state.attributes.get(ATTR_ENTITY_ID) == ["valve.bedroom_group"]

    # Test controlling the nested group
    async with asyncio.timeout(0.5):
        await hass.services.async_call(
            VALVE_DOMAIN,
            SERVICE_CLOSE_VALVE,
            {ATTR_ENTITY_ID: "valve.nested_group"},
            blocking=True,
        )
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.CLOSING
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.CLOSING
    assert hass.states.get("valve.bedroom_group").state == ValveState.CLOSING
    assert hass.states.get("valve.nested_group").state == ValveState.CLOSING