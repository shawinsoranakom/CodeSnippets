async def test_service_call_to_child(hass: HomeAssistant, mock_states) -> None:
    """Test service calls that should be routed to a child."""
    config = validate_config(CONFIG_CHILDREN_ONLY)

    ump = universal.UniversalMediaPlayer(hass, config)
    ump.entity_id = media_player.ENTITY_ID_FORMAT.format(config["name"])
    await ump.async_update()

    mock_states.mock_mp_2._state = STATE_PLAYING
    mock_states.mock_mp_2.async_schedule_update_ha_state()
    await hass.async_block_till_done()
    await ump.async_update()

    await ump.async_turn_off()
    assert len(mock_states.mock_mp_2.service_calls["turn_off"]) == 1

    await ump.async_turn_on()
    assert len(mock_states.mock_mp_2.service_calls["turn_on"]) == 1

    await ump.async_mute_volume(True)
    assert len(mock_states.mock_mp_2.service_calls["mute_volume"]) == 1

    await ump.async_set_volume_level(0.5)
    assert len(mock_states.mock_mp_2.service_calls["set_volume_level"]) == 1

    await ump.async_media_play()
    assert len(mock_states.mock_mp_2.service_calls["media_play"]) == 1

    await ump.async_media_pause()
    assert len(mock_states.mock_mp_2.service_calls["media_pause"]) == 1

    await ump.async_media_stop()
    assert len(mock_states.mock_mp_2.service_calls["media_stop"]) == 1

    await ump.async_media_previous_track()
    assert len(mock_states.mock_mp_2.service_calls["media_previous_track"]) == 1

    await ump.async_media_next_track()
    assert len(mock_states.mock_mp_2.service_calls["media_next_track"]) == 1

    await ump.async_media_seek(100)
    assert len(mock_states.mock_mp_2.service_calls["media_seek"]) == 1

    await ump.async_play_media("movie", "batman")
    assert len(mock_states.mock_mp_2.service_calls["play_media"]) == 1

    await ump.async_volume_up()
    assert len(mock_states.mock_mp_2.service_calls["volume_up"]) == 1

    await ump.async_volume_down()
    assert len(mock_states.mock_mp_2.service_calls["volume_down"]) == 1

    await ump.async_media_play_pause()
    assert len(mock_states.mock_mp_2.service_calls["media_play_pause"]) == 1

    await ump.async_select_sound_mode("music")
    assert len(mock_states.mock_mp_2.service_calls["select_sound_mode"]) == 1

    await ump.async_select_source("dvd")
    assert len(mock_states.mock_mp_2.service_calls["select_source"]) == 1

    await ump.async_clear_playlist()
    assert len(mock_states.mock_mp_2.service_calls["clear_playlist"]) == 1

    await ump.async_set_repeat(True)
    assert len(mock_states.mock_mp_2.service_calls["repeat_set"]) == 1

    await ump.async_set_shuffle(True)
    assert len(mock_states.mock_mp_2.service_calls["shuffle_set"]) == 1

    await ump.async_toggle()
    # Delegate to turn_off
    assert len(mock_states.mock_mp_2.service_calls["turn_off"]) == 2