async def test_select_children(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mocked_feature_select: Feature,
) -> None:
    """Test select children."""
    mocked_feature = mocked_feature_select
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    plug = _mocked_device(
        alias="my_plug",
        features=[mocked_feature],
        children=_mocked_strip_children(features=[mocked_feature]),
    )
    with _patch_discovery(device=plug), _patch_connect(device=plug):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "select.my_plug_light_preset"
    entity = entity_registry.async_get(entity_id)
    assert entity
    device = device_registry.async_get(entity.device_id)

    for plug_id in range(2):
        child_entity_id = f"select.my_plug_plug{plug_id}_light_preset"
        child_entity = entity_registry.async_get(child_entity_id)
        assert child_entity
        assert child_entity.unique_id == f"PLUG{plug_id}DEVICEID_{mocked_feature.id}"
        assert child_entity.device_id != entity.device_id
        child_device = device_registry.async_get(child_entity.device_id)
        assert child_device
        assert child_device.via_device_id == device.id