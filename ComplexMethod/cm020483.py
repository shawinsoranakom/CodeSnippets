async def test_sensor_children_on_parent(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test a WallSwitch sensor entities are added to parent."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    feature = _mocked_feature(
        "consumption_this_month",
        value=5.2,
        # integration should ignore name and use the value from strings.json:
        # This month's consumption
        name="Consumption for month",
        type_=Feature.Type.Sensor,
        category=Feature.Category.Primary,
        unit="A",
        precision_hint=2,
    )
    plug = _mocked_device(
        alias="my_plug",
        features=[feature],
        children=_mocked_strip_children(features=[feature]),
        device_type=Device.Type.WallSwitch,
    )
    with _patch_discovery(device=plug), _patch_connect(device=plug):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_id = "sensor.my_plug_this_month_s_consumption"
    entity = entity_registry.async_get(entity_id)
    assert entity
    device = device_registry.async_get(entity.device_id)

    for plug_id in range(2):
        child_entity_id = f"sensor.my_plug_plug{plug_id}_this_month_s_consumption"
        child_entity = entity_registry.async_get(child_entity_id)
        assert child_entity
        assert child_entity.unique_id == f"PLUG{plug_id}DEVICEID_consumption_this_month"
        child_device = device_registry.async_get(child_entity.device_id)
        assert child_device

        assert child_entity.device_id == entity.device_id
        assert child_device.connections == device.connections