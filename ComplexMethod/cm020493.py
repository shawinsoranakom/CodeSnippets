async def test_number_children(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test number children."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    new_feature = _mocked_feature(
        "temperature_offset",
        value=10,
        name="Some number",
        type_=Feature.Type.Number,
        category=Feature.Category.Config,
        minimum_value=1,
        maximum_value=100,
    )
    plug = _mocked_device(
        alias="my_plug",
        features=[new_feature],
        children=_mocked_strip_children(features=[new_feature]),
    )
    with _patch_discovery(device=plug), _patch_connect(device=plug):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "number.my_plug_temperature_offset"
    entity = entity_registry.async_get(entity_id)
    assert entity
    device = device_registry.async_get(entity.device_id)

    for plug_id in range(2):
        child_entity_id = f"number.my_plug_plug{plug_id}_temperature_offset"
        child_entity = entity_registry.async_get(child_entity_id)
        assert child_entity
        assert child_entity.unique_id == f"PLUG{plug_id}DEVICEID_temperature_offset"
        assert child_entity.device_id != entity.device_id
        child_device = device_registry.async_get(child_entity.device_id)
        assert child_device
        assert child_device.via_device_id == device.id