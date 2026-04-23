async def test_media_player_television_duplicate_sources(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test if television accessory with duplicate sources."""
    entity_id = "media_player.television"
    sources = ["MUSIC", "HDMI", "SCREEN MIRRORING", "HDMI", "MUSIC"]
    hass.states.async_set(
        entity_id,
        None,
        {
            ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.TV,
            ATTR_SUPPORTED_FEATURES: 3469,
            ATTR_MEDIA_VOLUME_MUTED: False,
            ATTR_INPUT_SOURCE: "HDMI",
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
    assert acc.char_input_source.value == 1
    assert acc.char_mute.value is False

    hass.states.async_set(
        entity_id,
        None,
        {
            ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.TV,
            ATTR_SUPPORTED_FEATURES: 3469,
            ATTR_MEDIA_VOLUME_MUTED: False,
            ATTR_INPUT_SOURCE: "MUSIC",
            ATTR_INPUT_SOURCE_LIST: sources,
        },
    )
    await hass.async_block_till_done()
    assert acc.char_input_source.value == 0