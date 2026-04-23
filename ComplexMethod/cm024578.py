async def test_zone_attributes(
    hass: HomeAssistant,
    device1_config: MockConfigEntry,
    device2_config: MockConfigEntry,
    device1_requests_mock_standby,
    device2_requests_mock_standby,
) -> None:
    """Test zone attributes."""
    await setup_soundtouch(hass, device1_config, device2_config)

    # Fast-forward time to allow all entities to be set up and updated again
    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    entity_1_state = hass.states.get(DEVICE_1_ENTITY_ID)
    assert entity_1_state.attributes[ATTR_SOUNDTOUCH_ZONE]["is_master"]
    assert (
        entity_1_state.attributes[ATTR_SOUNDTOUCH_ZONE]["master"] == DEVICE_1_ENTITY_ID
    )
    assert entity_1_state.attributes[ATTR_SOUNDTOUCH_ZONE]["slaves"] == [
        DEVICE_2_ENTITY_ID
    ]
    assert entity_1_state.attributes[ATTR_SOUNDTOUCH_GROUP] == [
        DEVICE_1_ENTITY_ID,
        DEVICE_2_ENTITY_ID,
    ]

    entity_2_state = hass.states.get(DEVICE_2_ENTITY_ID)
    assert not entity_2_state.attributes[ATTR_SOUNDTOUCH_ZONE]["is_master"]
    assert (
        entity_2_state.attributes[ATTR_SOUNDTOUCH_ZONE]["master"] == DEVICE_1_ENTITY_ID
    )
    assert entity_2_state.attributes[ATTR_SOUNDTOUCH_ZONE]["slaves"] == [
        DEVICE_2_ENTITY_ID
    ]
    assert entity_2_state.attributes[ATTR_SOUNDTOUCH_GROUP] == [
        DEVICE_1_ENTITY_ID,
        DEVICE_2_ENTITY_ID,
    ]