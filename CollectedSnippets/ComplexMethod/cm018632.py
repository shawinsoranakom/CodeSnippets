async def test_websocket_events(hass: HomeAssistant) -> None:
    """Test websocket events."""
    mocked_device = _create_mocked_device()
    entry = MockConfigEntry(domain=songpal.DOMAIN, data=CONF_DATA)
    entry.add_to_hass(hass)

    with _patch_media_player_device(mocked_device):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    mocked_device.listen_notifications.assert_called_once()
    assert mocked_device.on_notification.call_count == 5

    notification_callbacks = mocked_device.notification_callbacks

    volume_change = MagicMock()
    volume_change.mute = True
    volume_change.volume = 20
    await notification_callbacks[VolumeChange](volume_change)
    attributes = _get_attributes(hass)
    assert attributes["is_volume_muted"] is True
    assert attributes["volume_level"] == 0.2

    content_change = MagicMock()
    content_change.is_input = False
    content_change.uri = "uri1"
    await notification_callbacks[ContentChange](content_change)
    assert _get_attributes(hass)["source"] == "title2"
    content_change.is_input = True
    await notification_callbacks[ContentChange](content_change)
    assert _get_attributes(hass)["source"] == "title1"

    sound_mode_change = MagicMock()
    sound_mode_change.target = "soundField"
    sound_mode_change.currentValue = "sound_mode1"
    await notification_callbacks[SettingChange](sound_mode_change)
    assert _get_attributes(hass)["sound_mode"] == "Sound Mode 1"
    sound_mode_change.currentValue = "sound_mode2"
    await notification_callbacks[SettingChange](sound_mode_change)
    assert _get_attributes(hass)["sound_mode"] == "Sound Mode 2"

    power_change = MagicMock()
    power_change.status = False
    await notification_callbacks[PowerChange](power_change)
    assert hass.states.get(ENTITY_ID).state == STATE_OFF