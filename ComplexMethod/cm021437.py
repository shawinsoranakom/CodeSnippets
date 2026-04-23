async def test_volume_services(hass: HomeAssistant) -> None:
    """Test the volume service."""
    assert await async_setup_component(
        hass, MP_DOMAIN, {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 1.0

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_VOLUME_SET,
            {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_LEVEL: None},
            blocking=True,
        )

    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 1.0

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_SET,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_LEVEL: 0.5},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 0.5

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_DOWN,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 0.4

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_UP,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_VOLUME_LEVEL) == 0.5

    assert state.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is False

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_VOLUME_MUTE,
            {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_MUTED: None},
            blocking=True,
        )

    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is False

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_VOLUME_MUTE,
        {ATTR_ENTITY_ID: TEST_ENTITY_ID, ATTR_MEDIA_VOLUME_MUTED: True},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(TEST_ENTITY_ID)
    assert state.attributes.get(ATTR_MEDIA_VOLUME_MUTED) is True