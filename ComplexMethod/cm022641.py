async def test_media_player_television(
    hass: HomeAssistant,
    hk_driver,
    events: list[Event],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test if television accessory and HA are updated accordingly."""
    entity_id = "media_player.television"

    # Supports 'select_source', 'volume_step', 'turn_on', 'turn_off',
    #       'volume_mute', 'volume_set', 'pause'
    base_attrs = {
        ATTR_DEVICE_CLASS: MediaPlayerDeviceClass.TV,
        ATTR_SUPPORTED_FEATURES: 3469,
        ATTR_MEDIA_VOLUME_MUTED: False,
        ATTR_INPUT_SOURCE_LIST: ["HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4"],
    }
    hass.states.async_set(
        entity_id,
        None,
        base_attrs,
    )
    await hass.async_block_till_done()
    acc = TelevisionMediaPlayer(hass, hk_driver, "MediaPlayer", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 31  # Television

    assert acc.char_active.value == 0
    assert acc.char_remote_key.value == 0
    assert acc.char_input_source.value == 0
    assert acc.char_mute.value is False

    hass.states.async_set(
        entity_id, STATE_ON, {**base_attrs, ATTR_MEDIA_VOLUME_MUTED: True}
    )
    await hass.async_block_till_done()
    assert acc.char_active.value == 1
    assert acc.char_mute.value is True

    hass.states.async_set(entity_id, STATE_OFF, base_attrs)
    await hass.async_block_till_done()
    assert acc.char_active.value == 0

    hass.states.async_set(entity_id, STATE_ON, base_attrs)
    await hass.async_block_till_done()
    assert acc.char_active.value == 1

    hass.states.async_set(entity_id, STATE_STANDBY, base_attrs)
    await hass.async_block_till_done()
    assert acc.char_active.value == 0

    hass.states.async_set(
        entity_id, STATE_ON, {**base_attrs, ATTR_INPUT_SOURCE: "HDMI 2"}
    )
    await hass.async_block_till_done()
    assert acc.char_input_source.value == 1

    hass.states.async_set(
        entity_id, STATE_ON, {**base_attrs, ATTR_INPUT_SOURCE: "HDMI 3"}
    )
    await hass.async_block_till_done()
    assert acc.char_input_source.value == 2

    hass.states.async_set(
        entity_id, STATE_ON, {**base_attrs, ATTR_INPUT_SOURCE: "HDMI 5"}
    )
    await hass.async_block_till_done()
    assert acc.char_input_source.value == 0
    assert caplog.records[-2].levelname == "DEBUG"

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "turn_on")
    call_turn_off = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "turn_off")
    call_media_play = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "media_play")
    call_media_pause = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "media_pause")
    call_media_play_pause = async_mock_service(
        hass, MEDIA_PLAYER_DOMAIN, "media_play_pause"
    )
    call_toggle_mute = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "volume_mute")
    call_select_source = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "select_source")
    call_volume_up = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "volume_up")
    call_volume_down = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "volume_down")
    call_volume_set = async_mock_service(hass, MEDIA_PLAYER_DOMAIN, "volume_set")

    acc.char_active.client_update_value(1)
    await hass.async_block_till_done()
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_active.client_update_value(0)
    await hass.async_block_till_done()
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_remote_key.client_update_value(11)
    await hass.async_block_till_done()
    assert call_media_play_pause
    assert call_media_play_pause[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 3
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(entity_id, STATE_PLAYING)
    await hass.async_block_till_done()
    acc.char_remote_key.client_update_value(11)
    await hass.async_block_till_done()
    assert call_media_pause
    assert call_media_pause[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_remote_key.client_update_value(10)
    await hass.async_block_till_done()
    assert len(events) == 4
    assert events[-1].data[ATTR_VALUE] is None

    hass.states.async_set(entity_id, STATE_PAUSED)
    await hass.async_block_till_done()
    acc.char_remote_key.client_update_value(11)
    await hass.async_block_till_done()
    assert call_media_play
    assert call_media_play[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 5
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_mute.client_update_value(True)
    await hass.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[0].data[ATTR_MEDIA_VOLUME_MUTED] is True
    assert len(events) == 6
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_mute.client_update_value(False)
    await hass.async_block_till_done()
    assert call_toggle_mute
    assert call_toggle_mute[1].data[ATTR_ENTITY_ID] == entity_id
    assert call_toggle_mute[1].data[ATTR_MEDIA_VOLUME_MUTED] is False
    assert len(events) == 7
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_input_source.client_update_value(1)
    await hass.async_block_till_done()
    assert call_select_source
    assert call_select_source[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_select_source[0].data[ATTR_INPUT_SOURCE] == "HDMI 2"
    assert len(events) == 8
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_volume_selector.client_update_value(0)
    await hass.async_block_till_done()
    assert call_volume_up
    assert call_volume_up[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 9
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_volume_selector.client_update_value(1)
    await hass.async_block_till_done()
    assert call_volume_down
    assert call_volume_down[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 10
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_volume.client_update_value(20)
    await hass.async_block_till_done()
    assert call_volume_set[0]
    assert call_volume_set[0].data[ATTR_ENTITY_ID] == entity_id
    assert call_volume_set[0].data[ATTR_MEDIA_VOLUME_LEVEL] == 20
    assert len(events) == 11
    assert events[-1].data[ATTR_VALUE] is None

    events = []

    def listener(event):
        events.append(event)

    hass.bus.async_listen(EVENT_HOMEKIT_TV_REMOTE_KEY_PRESSED, listener)

    with pytest.raises(ValueError):
        acc.char_remote_key.client_update_value(20)

    acc.char_remote_key.client_update_value(7)
    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].data[ATTR_KEY_NAME] == KEY_ARROW_RIGHT