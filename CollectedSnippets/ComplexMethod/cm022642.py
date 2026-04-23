async def test_media_player_television_basic(
    hass: HomeAssistant, hk_driver, caplog: pytest.LogCaptureFixture
) -> None:
    """Test if basic television accessory and HA are updated accordingly."""
    entity_id = "media_player.television"
    base_attrs = {
        ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.TV,
        ATTR_SUPPORTED_FEATURES: 384,
    }
    # Supports turn_on', 'turn_off'
    hass.states.async_set(
        entity_id,
        None,
        base_attrs,
    )
    await hass.async_block_till_done()
    acc = TelevisionMediaPlayer(hass, hk_driver, "MediaPlayer", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.chars_tv == [CHAR_REMOTE_KEY]
    assert acc.chars_speaker == []
    assert acc.support_select_source is False

    hass.states.async_set(
        entity_id, STATE_ON, {**base_attrs, ATTR_MEDIA_VOLUME_MUTED: True}
    )
    await hass.async_block_till_done()
    assert acc.char_active.value == 1

    hass.states.async_set(entity_id, STATE_OFF, base_attrs)
    await hass.async_block_till_done()
    assert acc.char_active.value == 0

    hass.states.async_set(
        entity_id, STATE_ON, {**base_attrs, ATTR_INPUT_SOURCE: "HDMI 3"}
    )
    await hass.async_block_till_done()
    assert acc.char_active.value == 1

    assert not caplog.messages or "Error" not in caplog.messages[-1]