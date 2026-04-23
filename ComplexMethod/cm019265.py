async def test_nested_group(hass: HomeAssistant) -> None:
    """Test nested media group."""
    await async_setup_component(
        hass,
        MEDIA_DOMAIN,
        {
            MEDIA_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "entities": ["media_player.group_1"],
                    "name": "Nested Group",
                },
                {
                    "platform": DOMAIN,
                    "entities": ["media_player.bedroom", "media_player.kitchen"],
                    "name": "Group 1",
                },
            ]
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("media_player.group_1")
    assert state is not None
    assert state.state == STATE_PLAYING
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        "media_player.bedroom",
        "media_player.kitchen",
    ]

    state = hass.states.get("media_player.nested_group")
    assert state is not None
    assert state.state == STATE_PLAYING
    assert state.attributes.get(ATTR_ENTITY_ID) == ["media_player.group_1"]

    # Test controlling the nested group
    async with asyncio.timeout(0.5):
        await hass.services.async_call(
            MEDIA_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "media_player.group_1"},
            blocking=True,
        )

    await hass.async_block_till_done()
    assert hass.states.get("media_player.bedroom").state == STATE_OFF
    assert hass.states.get("media_player.kitchen").state == STATE_OFF
    assert hass.states.get("media_player.group_1").state == STATE_OFF
    assert hass.states.get("media_player.nested_group").state == STATE_OFF