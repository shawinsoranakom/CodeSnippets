async def test_nested_group(hass: HomeAssistant) -> None:
    """Test nested fan group."""
    await async_setup_component(
        hass,
        FAN_DOMAIN,
        {
            FAN_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": "group",
                    "entities": ["fan.bedroom_group"],
                    "name": "Nested Group",
                },
                {
                    "platform": "group",
                    CONF_ENTITIES: [
                        LIVING_ROOM_FAN_ENTITY_ID,
                        PERCENTAGE_FULL_FAN_ENTITY_ID,
                    ],
                    "name": "Bedroom Group",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("fan.bedroom_group")
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        LIVING_ROOM_FAN_ENTITY_ID,
        PERCENTAGE_FULL_FAN_ENTITY_ID,
    ]

    state = hass.states.get("fan.nested_group")
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ENTITY_ID) == ["fan.bedroom_group"]

    # Test controlling the nested group
    async with asyncio.timeout(0.5):
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "fan.nested_group"},
            blocking=True,
        )
    assert hass.states.get(LIVING_ROOM_FAN_ENTITY_ID).state == STATE_ON
    assert hass.states.get(PERCENTAGE_FULL_FAN_ENTITY_ID).state == STATE_ON
    assert hass.states.get("fan.bedroom_group").state == STATE_ON
    assert hass.states.get("fan.nested_group").state == STATE_ON