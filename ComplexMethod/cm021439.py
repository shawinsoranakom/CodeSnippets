async def test_prev_next_track(hass: HomeAssistant) -> None:
    """Test media_next_track and media_previous_track ."""
    assert await async_setup_component(
        hass, MP_DOMAIN, {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_TRACK) == 1

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_TRACK) == 2

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_TRACK) == 3

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_TRACK) == 2

    assert await async_setup_component(
        hass, MP_DOMAIN, {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    ent_id = "media_player.lounge_room"
    state = hass.states.get(ent_id)
    assert state.attributes.get(ATTR_MEDIA_EPISODE) == "1"

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_NEXT_TRACK,
        {ATTR_ENTITY_ID: ent_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(ent_id)
    assert state.attributes.get(ATTR_MEDIA_EPISODE) == "2"

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_MEDIA_PREVIOUS_TRACK,
        {ATTR_ENTITY_ID: ent_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(ent_id)
    assert state.attributes.get(ATTR_MEDIA_EPISODE) == "1"