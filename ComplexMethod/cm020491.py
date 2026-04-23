async def test_strip_blank_alias(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test a strip with blank parent alias."""
    already_migrated_config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.1"}, unique_id=MAC_ADDRESS
    )
    already_migrated_config_entry.add_to_hass(hass)
    strip = _mocked_device(
        alias="",
        model="KS123",
        children=_mocked_strip_children(features=["state", "led"], alias=""),
        features=["state", "led"],
    )
    with _patch_discovery(device=strip), _patch_connect(device=strip):
        await hass.config_entries.async_setup(already_migrated_config_entry.entry_id)
        await hass.async_block_till_done()

    strip_entity_id = "switch.unnamed_ks123"
    state = hass.states.get(strip_entity_id)
    assert state.name == "Unnamed KS123"
    reg_ent = entity_registry.async_get(strip_entity_id)
    assert reg_ent
    reg_dev = device_registry.async_get(reg_ent.device_id)
    assert reg_dev
    assert reg_dev.name == "Unnamed KS123"

    for plug_id in range(2):
        entity_id = f"switch.unnamed_ks123_stripsocket_{plug_id + 1}"
        state = hass.states.get(entity_id)
        assert state.name == f"Unnamed KS123 Stripsocket {plug_id + 1}"

        reg_ent = entity_registry.async_get(entity_id)
        assert reg_ent
        reg_dev = device_registry.async_get(reg_ent.device_id)
        assert reg_dev
        # Switch is a primary feature so entities go on the parent device.
        assert reg_dev.name == "Unnamed KS123"