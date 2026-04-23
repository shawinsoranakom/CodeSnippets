async def test_switch_attributes(
    hass: HomeAssistant,
    async_autosetup_sonos,
    soco,
    fire_zgs_event,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test for correct Sonos switch states."""
    alarm = entity_registry.entities["switch.sonos_alarm_14"]
    alarm_state = hass.states.get(alarm.entity_id)
    assert alarm_state.state == STATE_ON
    assert alarm_state.attributes.get(ATTR_TIME) == "07:00:00"
    assert alarm_state.attributes.get(ATTR_ID) == "14"
    assert alarm_state.attributes.get(ATTR_DURATION) == "02:00:00"
    assert alarm_state.attributes.get(ATTR_RECURRENCE) == "DAILY"
    assert alarm_state.attributes.get(ATTR_VOLUME) == 0.25
    assert alarm_state.attributes.get(ATTR_PLAY_MODE) == "SHUFFLE_NOREPEAT"
    assert not alarm_state.attributes.get(ATTR_INCLUDE_LINKED_ZONES)

    surround_music_full_volume = entity_registry.entities[
        "switch.zone_a_surround_music_full_volume"
    ]
    surround_music_full_volume_state = hass.states.get(
        surround_music_full_volume.entity_id
    )
    assert surround_music_full_volume_state.state == STATE_ON

    night_sound = entity_registry.entities["switch.zone_a_night_sound"]
    night_sound_state = hass.states.get(night_sound.entity_id)
    assert night_sound_state.state == STATE_ON

    loudness = entity_registry.entities["switch.zone_a_loudness"]
    loudness_state = hass.states.get(loudness.entity_id)
    assert loudness_state.state == STATE_ON

    speech_enhancement = entity_registry.entities["switch.zone_a_speech_enhancement"]
    speech_enhancement_state = hass.states.get(speech_enhancement.entity_id)
    assert speech_enhancement_state.state == STATE_ON

    crossfade = entity_registry.entities["switch.zone_a_crossfade"]
    crossfade_state = hass.states.get(crossfade.entity_id)
    assert crossfade_state.state == STATE_ON

    # Ensure switches are disabled
    status_light = entity_registry.entities["switch.zone_a_status_light"]
    assert hass.states.get(status_light.entity_id) is None

    touch_controls = entity_registry.entities["switch.zone_a_touch_controls"]
    assert hass.states.get(touch_controls.entity_id) is None

    sub_switch = entity_registry.entities["switch.zone_a_subwoofer_enabled"]
    sub_switch_state = hass.states.get(sub_switch.entity_id)
    assert sub_switch_state.state == STATE_OFF

    surround_switch = entity_registry.entities["switch.zone_a_surround_enabled"]
    surround_switch_state = hass.states.get(surround_switch.entity_id)
    assert surround_switch_state.state == STATE_ON

    # Enable disabled switches
    for entity in (status_light, touch_controls):
        entity_registry.async_update_entity(
            entity_id=entity.entity_id, disabled_by=None
        )
    await hass.async_block_till_done()

    # Fire event to cancel poll timer and avoid triggering errors during time jump
    service = soco.contentDirectory
    empty_event = SonosMockEvent(soco, service, {})
    subscription = service.subscribe.return_value
    subscription.callback(event=empty_event)
    await hass.async_block_till_done()

    # Mock shutdown calls during config entry reload
    with patch.object(hass.data[DATA_SONOS_DISCOVERY_MANAGER], "async_shutdown") as m:
        async_fire_time_changed(
            hass,
            dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
        )
        await hass.async_block_till_done(wait_background_tasks=True)
        assert m.called

    # Trigger subscription callback for speaker discovery
    await fire_zgs_event()
    await hass.async_block_till_done(wait_background_tasks=True)

    status_light_state = hass.states.get(status_light.entity_id)
    assert status_light_state.state == STATE_ON

    touch_controls = entity_registry.entities["switch.zone_a_touch_controls"]
    touch_controls_state = hass.states.get(touch_controls.entity_id)
    assert touch_controls_state.state == STATE_ON