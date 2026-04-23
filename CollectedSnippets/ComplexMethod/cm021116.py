def validate_default_camera_entity(
    hass: HomeAssistant,
    camera_obj: ProtectCamera,
    channel_id: int,
) -> str:
    """Validate a camera entity."""

    channel = camera_obj.channels[channel_id]

    camera_name = get_camera_base_name(channel)
    entity_name = f"{camera_obj.name} {camera_name}"
    unique_id = f"{camera_obj.mac}_{channel.id}"
    entity_id = f"camera.{entity_name.replace(' ', '_').lower()}"

    entity_registry = er.async_get(hass)
    entity = entity_registry.async_get(entity_id)
    assert entity
    assert entity.disabled is False
    assert entity.unique_id == unique_id

    device_registry = dr.async_get(hass)
    device = device_registry.async_get(entity.device_id)
    assert device
    assert device.manufacturer == "Ubiquiti"
    assert device.name == camera_obj.name
    assert device.model == camera_obj.market_name or camera_obj.type
    assert device.model_id == camera_obj.type

    return entity_id