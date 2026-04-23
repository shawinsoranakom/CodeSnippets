async def test_tv_restore(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, hk_driver
) -> None:
    """Test setting up an entity from state in the event registry."""
    hass.set_state(CoreState.not_running)

    entity_registry.async_get_or_create(
        "media_player",
        "generic",
        "1234",
        suggested_object_id="simple",
        original_device_class=MediaPlayerDeviceClass.TV,
    )
    entity_registry.async_get_or_create(
        "media_player",
        "generic",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={
            ATTR_INPUT_SOURCE_LIST: ["HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4"],
        },
        supported_features=3469,
        original_device_class=MediaPlayerDeviceClass.TV,
    )

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START, {})
    await hass.async_block_till_done()

    acc = TelevisionMediaPlayer(
        hass, hk_driver, "MediaPlayer", "media_player.simple", 2, None
    )
    assert acc.category == 31
    assert acc.chars_tv == [CHAR_REMOTE_KEY]
    assert acc.chars_speaker == []
    assert acc.support_select_source is False
    assert not hasattr(acc, "char_input_source")

    acc = TelevisionMediaPlayer(
        hass, hk_driver, "MediaPlayer", "media_player.all_info_set", 3, None
    )
    assert acc.category == 31
    assert acc.chars_tv == [CHAR_REMOTE_KEY]
    assert acc.chars_speaker == [
        "Name",
        "Active",
        "VolumeControlType",
        "VolumeSelector",
        "Volume",
    ]
    assert acc.support_select_source is True
    assert acc.char_input_source is not None