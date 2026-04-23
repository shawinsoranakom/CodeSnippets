async def test_media_player_television_unsafe_chars(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if television accessory with unsafe characters."""
    entity_id = "media_player.television"
    sources = ["MUSIC", "HDMI 3/ARC", "SCREEN MIRRORING", "HDMI 2/MHL", "HDMI", "MUSIC"]
    hass.states.async_set(
        entity_id,
        None,
        {
            ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.TV,
            ATTR_SUPPORTED_FEATURES: 3469,
            ATTR_MEDIA_VOLUME_MUTED: False,
            ATTR_INPUT_SOURCE: "HDMI 2/MHL",
            ATTR_INPUT_SOURCE_LIST: sources,
        },
    )
    await hass.async_block_till_done()
    acc = TelevisionMediaPlayer(hass, hk_driver, "MediaPlayer", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 31  # Television

    assert acc.char_active.value == 0
    assert acc.char_remote_key.value == 0
    assert acc.char_input_source.value == 3
    assert acc.char_mute.value is False

    hass.states.async_set(
        entity_id,
        None,
        {
            ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.TV,
            ATTR_SUPPORTED_FEATURES: 3469,
            ATTR_MEDIA_VOLUME_MUTED: False,
            ATTR_INPUT_SOURCE: "HDMI 3/ARC",
            ATTR_INPUT_SOURCE_LIST: sources,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_input_source.value == 1

    call_select_source = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "select_source")

    acc.char_input_source.client_update_value(3)
    await hass.async_block_till_done()
    assert call_select_source
    assert call_select_source[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_select_source[0].data[ATTR_INPUT_SOURCE] == "HDMI 2/MHL"
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    assert acc.char_input_source.value == 3

    acc.char_input_source.client_update_value(4)
    await hass.async_block_till_done()
    assert call_select_source
    assert call_select_source[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_select_source[1].data[ATTR_INPUT_SOURCE] == "HDMI"
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    assert acc.char_input_source.value == 4