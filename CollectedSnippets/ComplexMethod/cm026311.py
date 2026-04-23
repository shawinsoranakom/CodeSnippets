async def set_chime_paired_doorbells(call: ServiceCall) -> None:
    """Set paired doorbells on chime."""
    ref = async_extract_referenced_entity_ids(call.hass, TargetSelection(call.data))
    entity_registry = er.async_get(call.hass)

    entity_id = ref.indirectly_referenced.pop()
    chime_button = entity_registry.async_get(entity_id)
    assert chime_button is not None
    assert chime_button.device_id is not None
    chime_mac = _async_unique_id_to_mac(chime_button.unique_id)

    instance = _async_get_ufp_instance(call.hass, chime_button.device_id)
    chime = instance.bootstrap.get_device_from_mac(chime_mac)
    chime = cast(Chime, chime)
    assert chime is not None

    call.data = ReadOnlyDict(call.data.get("doorbells") or {})
    doorbell_refs = async_extract_referenced_entity_ids(
        call.hass, TargetSelection(call.data)
    )
    doorbell_ids: set[str] = set()
    for camera_id in doorbell_refs.referenced | doorbell_refs.indirectly_referenced:
        doorbell_sensor = entity_registry.async_get(camera_id)
        assert doorbell_sensor is not None
        if (
            doorbell_sensor.platform != DOMAIN
            or doorbell_sensor.domain != Platform.BINARY_SENSOR
            or doorbell_sensor.original_device_class
            != BinarySensorDeviceClass.OCCUPANCY
        ):
            continue
        doorbell_mac = _async_unique_id_to_mac(doorbell_sensor.unique_id)
        camera = instance.bootstrap.get_device_from_mac(doorbell_mac)
        assert camera is not None
        doorbell_ids.add(camera.id)
    data_before_changed = chime.dict_with_excludes()
    chime.camera_ids = sorted(doorbell_ids)
    await chime.save_device(data_before_changed)