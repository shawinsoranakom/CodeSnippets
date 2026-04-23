async def test_volume_while_mute(hass: HomeAssistant) -> None:
    """Test increasing volume by one."""
    ws66i = MockWs66i()
    _ = await _setup_ws66i(hass, ws66i)

    # Set vol to a known value
    await _call_media_player_service(
        hass, SERVICE_VOLUME_SET, {"entity_id": ZONE_1_ID, "volume_level": 0.0}
    )
    assert ws66i.zones[11].volume == 0

    # Set mute to a known value, False
    await _call_media_player_service(
        hass, SERVICE_VOLUME_MUTE, {"entity_id": ZONE_1_ID, "is_volume_muted": False}
    )
    assert not ws66i.zones[11].mute

    # Mute the zone
    await _call_media_player_service(
        hass, SERVICE_VOLUME_MUTE, {"entity_id": ZONE_1_ID, "is_volume_muted": True}
    )
    assert ws66i.zones[11].mute

    # Increase volume. Mute state should go back to unmutted
    await _call_media_player_service(hass, SERVICE_VOLUME_UP, {"entity_id": ZONE_1_ID})
    assert ws66i.zones[11].volume == 1
    assert not ws66i.zones[11].mute

    # Mute the zone again
    await _call_media_player_service(
        hass, SERVICE_VOLUME_MUTE, {"entity_id": ZONE_1_ID, "is_volume_muted": True}
    )
    assert ws66i.zones[11].mute

    # Decrease volume. Mute state should go back to unmutted
    await _call_media_player_service(
        hass, SERVICE_VOLUME_DOWN, {"entity_id": ZONE_1_ID}
    )
    assert ws66i.zones[11].volume == 0
    assert not ws66i.zones[11].mute

    # Mute the zone again
    await _call_media_player_service(
        hass, SERVICE_VOLUME_MUTE, {"entity_id": ZONE_1_ID, "is_volume_muted": True}
    )
    assert ws66i.zones[11].mute

    # Set to max volume. Mute state should go back to unmutted
    await _call_media_player_service(
        hass, SERVICE_VOLUME_SET, {"entity_id": ZONE_1_ID, "volume_level": 1.0}
    )
    assert ws66i.zones[11].volume == MAX_VOL
    assert not ws66i.zones[11].mute