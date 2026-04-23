async def test_nested_group(hass: HomeAssistant) -> None:
    """Test nested cover group."""
    await async_setup_component(
        hass,
        COVER_DOMAIN,
        {
            COVER_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": "group",
                    "entities": ["cover.bedroom_group"],
                    "name": "Nested Group",
                },
                {
                    "platform": "group",
                    CONF_ENTITIES: [DEMO_COVER_POS, DEMO_COVER_TILT],
                    "name": "Bedroom Group",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("cover.bedroom_group")
    assert state is not None
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_ENTITY_ID) == [DEMO_COVER_POS, DEMO_COVER_TILT]

    state = hass.states.get("cover.nested_group")
    assert state is not None
    assert state.state == CoverState.OPEN
    assert state.attributes.get(ATTR_ENTITY_ID) == ["cover.bedroom_group"]

    # Test controlling the nested group
    async with asyncio.timeout(0.5):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: "cover.nested_group"},
            blocking=True,
        )
    assert hass.states.get(DEMO_COVER_POS).state == CoverState.CLOSING
    assert hass.states.get(DEMO_COVER_TILT).state == CoverState.CLOSING
    assert hass.states.get("cover.bedroom_group").state == CoverState.CLOSING
    assert hass.states.get("cover.nested_group").state == CoverState.CLOSING