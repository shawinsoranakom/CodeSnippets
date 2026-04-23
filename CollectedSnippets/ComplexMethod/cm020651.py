async def test_overrides(hass: HomeAssistant, config_children_and_attr) -> None:
    """Test overrides."""
    config = copy(config_children_and_attr)
    excmd = {"service": "test.override", "data": {}}
    config["name"] = "overridden"
    config["commands"] = {
        "turn_on": excmd,
        "turn_off": excmd,
        "volume_up": excmd,
        "volume_down": excmd,
        "volume_mute": excmd,
        "volume_set": excmd,
        "select_sound_mode": excmd,
        "select_source": excmd,
        "repeat_set": excmd,
        "shuffle_set": excmd,
        "media_play": excmd,
        "media_play_pause": excmd,
        "media_pause": excmd,
        "media_stop": excmd,
        "media_next_track": excmd,
        "media_previous_track": excmd,
        "clear_playlist": excmd,
        "play_media": excmd,
        "toggle": excmd,
        "entity_picture": excmd,
    }
    await async_setup_component(hass, "media_player", {"media_player": config})
    await hass.async_block_till_done()

    service = async_mock_service(hass, "test", "override")
    await hass.services.async_call(
        "media_player",
        "turn_on",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 1
    await hass.services.async_call(
        "media_player",
        "turn_off",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 2
    await hass.services.async_call(
        "media_player",
        "volume_up",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 3
    await hass.services.async_call(
        "media_player",
        "volume_down",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 4
    await hass.services.async_call(
        "media_player",
        "volume_mute",
        service_data={
            "entity_id": "media_player.overridden",
            "is_volume_muted": True,
        },
        blocking=True,
    )
    assert len(service) == 5
    await hass.services.async_call(
        "media_player",
        "volume_set",
        service_data={"entity_id": "media_player.overridden", "volume_level": 1},
        blocking=True,
    )
    assert len(service) == 6
    await hass.services.async_call(
        "media_player",
        "select_sound_mode",
        service_data={
            "entity_id": "media_player.overridden",
            "sound_mode": "music",
        },
        blocking=True,
    )
    assert len(service) == 7
    await hass.services.async_call(
        "media_player",
        "select_source",
        service_data={"entity_id": "media_player.overridden", "source": "video1"},
        blocking=True,
    )
    assert len(service) == 8
    await hass.services.async_call(
        "media_player",
        "repeat_set",
        service_data={"entity_id": "media_player.overridden", "repeat": "all"},
        blocking=True,
    )
    assert len(service) == 9
    await hass.services.async_call(
        "media_player",
        "shuffle_set",
        service_data={"entity_id": "media_player.overridden", "shuffle": True},
        blocking=True,
    )
    assert len(service) == 10
    await hass.services.async_call(
        "media_player",
        "media_play",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 11
    await hass.services.async_call(
        "media_player",
        "media_pause",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 12
    await hass.services.async_call(
        "media_player",
        "media_stop",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 13
    await hass.services.async_call(
        "media_player",
        "media_next_track",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 14
    await hass.services.async_call(
        "media_player",
        "media_previous_track",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 15
    await hass.services.async_call(
        "media_player",
        "clear_playlist",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 16
    await hass.services.async_call(
        "media_player",
        "media_play_pause",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 17
    await hass.services.async_call(
        "media_player",
        "play_media",
        service_data={
            "entity_id": "media_player.overridden",
            "media_content_id": 1,
            "media_content_type": "channel",
        },
        blocking=True,
    )
    assert len(service) == 18
    await hass.services.async_call(
        "media_player",
        "toggle",
        service_data={"entity_id": "media_player.overridden"},
        blocking=True,
    )
    assert len(service) == 19