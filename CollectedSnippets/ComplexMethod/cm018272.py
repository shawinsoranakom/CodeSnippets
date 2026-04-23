async def test_cleanup_button(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    fc_class_mock,
    fh_class_mock,
    fs_class_mock,
) -> None:
    """Test cleanup of orphan devices."""

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED

    # check if tracked device is registered properly
    device = device_registry.async_get_device(
        connections={("mac", "aa:bb:cc:00:11:22")}
    )
    assert device

    entities = [
        entity
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        if entity.unique_id.startswith("AA:BB:CC:00:11:22")
    ]
    assert entities
    assert len(entities) == 3

    # removed tracked device and trigger cleanup
    host_attributes = deepcopy(MOCK_HOST_ATTRIBUTES_DATA)
    host_attributes.pop(0)
    fh_class_mock.get_hosts_attributes.return_value = host_attributes

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.mock_title_cleanup"},
        blocking=True,
    )

    await hass.async_block_till_done(wait_background_tasks=True)

    # check if orphan tracked device is removed
    device = device_registry.async_get_device(
        connections={("mac", "aa:bb:cc:00:11:22")}
    )
    assert not device

    entities = [
        entity
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        if entity.unique_id.startswith("AA:BB:CC:00:11:22")
    ]
    assert not entities