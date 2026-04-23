async def test_entity_registry(
    hass: HomeAssistant, async_autosetup_sonos, entity_registry: er.EntityRegistry
) -> None:
    """Test sonos device with alarm registered in the device registry."""
    assert "media_player.zone_a" in entity_registry.entities
    assert "switch.sonos_alarm_14" in entity_registry.entities
    assert "switch.zone_a_status_light" in entity_registry.entities
    assert "switch.zone_a_loudness" in entity_registry.entities
    assert "switch.zone_a_night_sound" in entity_registry.entities
    assert "switch.zone_a_speech_enhancement" in entity_registry.entities
    assert "switch.zone_a_subwoofer_enabled" in entity_registry.entities
    assert "switch.zone_a_surround_enabled" in entity_registry.entities
    assert "switch.zone_a_touch_controls" in entity_registry.entities