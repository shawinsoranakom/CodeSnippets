async def test_sensors(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_device: MagicMock
) -> None:
    """Test sensors."""
    entity = hass.states.get(f"{ENTITY_ID}_media_location")
    entry = entity_registry.async_get(f"{ENTITY_ID}_media_location")
    assert entity
    assert entity.state == "none"
    assert (
        entity.attributes.get(ATTR_FRIENDLY_NAME) == f"{FRIENDLY_NAME} Media location"
    )
    assert entry
    assert entry.unique_id == f"{MOCK_SERIAL}-media_location"

    entity = hass.states.get(f"{ENTITY_ID}_play_status")
    entry = entity_registry.async_get(f"{ENTITY_ID}_play_status")
    assert entity
    assert entity.state == "none"
    assert entity.attributes.get(ATTR_FRIENDLY_NAME) == f"{FRIENDLY_NAME} Play status"
    assert entry
    assert entry.unique_id == f"{MOCK_SERIAL}-play_status"

    mock_device.movie.play_status = kaleidescape_const.PLAY_STATUS_PLAYING
    mock_device.dispatcher.send(kaleidescape_const.PLAY_STATUS)
    await hass.async_block_till_done()
    entity = hass.states.get(f"{ENTITY_ID}_play_status")
    assert entity is not None
    assert entity.state == "playing"