async def test_button_children(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
    mocked_feature_button: Feature,
    create_deprecated_button_entities,
    create_deprecated_child_button_entities,
) -> None:
    """Test button children."""
    mocked_feature = mocked_feature_button
    plug = _mocked_device(
        alias="my_device",
        features=[mocked_feature],
        children=_mocked_strip_children(features=[mocked_feature]),
    )
    with _patch_discovery(device=plug), _patch_connect(device=plug):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "button.my_device_test_alarm"
    entity = entity_registry.async_get(entity_id)
    assert entity
    device = device_registry.async_get(entity.device_id)

    for plug_id in range(2):
        child_entity_id = f"button.my_device_plug{plug_id}_test_alarm"
        child_entity = entity_registry.async_get(child_entity_id)
        assert child_entity
        assert child_entity.unique_id == f"PLUG{plug_id}DEVICEID_{mocked_feature.id}"
        assert child_entity.device_id != entity.device_id
        child_device = device_registry.async_get(child_entity.device_id)
        assert child_device
        assert child_device.via_device_id == device.id