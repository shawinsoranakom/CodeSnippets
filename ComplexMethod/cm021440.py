async def test_play_media(hass: HomeAssistant) -> None:
    """Test play_media ."""
    assert await async_setup_component(
        hass, MP_DOMAIN, {"media_player": {"platform": "demo"}}
    )
    await hass.async_block_till_done()

    ent_id = "media_player.living_room"
    state = hass.states.get(ent_id)
    assert (
        MediaPlayerEntityFeature.PLAY_MEDIA
        & state.attributes.get(ATTR_SUPPORTED_FEATURES)
        > 0
    )
    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) is not None

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_PLAY_MEDIA,
            {ATTR_ENTITY_ID: ent_id, ATTR_MEDIA_CONTENT_ID: "some_id"},
            blocking=True,
        )
    state = hass.states.get(ent_id)
    assert (
        MediaPlayerEntityFeature.PLAY_MEDIA
        & state.attributes.get(ATTR_SUPPORTED_FEATURES)
        > 0
    )
    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) != "some_id"

    await hass.services.async_call(
        MP_DOMAIN,
        SERVICE_PLAY_MEDIA,
        {
            ATTR_ENTITY_ID: ent_id,
            ATTR_MEDIA_CONTENT_TYPE: "youtube",
            ATTR_MEDIA_CONTENT_ID: "some_id",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get(ent_id)
    assert (
        MediaPlayerEntityFeature.PLAY_MEDIA
        & state.attributes.get(ATTR_SUPPORTED_FEATURES)
        > 0
    )
    assert state.attributes.get(ATTR_MEDIA_CONTENT_ID) == "some_id"