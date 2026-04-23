def validate_common_camera_state(
    hass: HomeAssistant,
    channel: CameraChannel,
    entity_id: str,
    features: int = CameraEntityFeature.STREAM,
):
    """Validate state that is common to all camera entity, regardless of type."""
    entity_state = hass.states.get(entity_id)
    assert entity_state
    assert entity_state.attributes[ATTR_ATTRIBUTION] == DEFAULT_ATTRIBUTION
    assert entity_state.attributes[ATTR_SUPPORTED_FEATURES] == features
    assert entity_state.attributes[ATTR_WIDTH] == channel.width
    assert entity_state.attributes[ATTR_HEIGHT] == channel.height
    assert entity_state.attributes[ATTR_FPS] == channel.fps
    assert entity_state.attributes[ATTR_BITRATE] == channel.bitrate
    assert entity_state.attributes[ATTR_CHANNEL_ID] == channel.id