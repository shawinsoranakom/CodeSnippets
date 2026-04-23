async def test_change_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    config_entry_options: dict[str, str],
    config_user_input: dict[str, str],
) -> None:
    """Test the link between the device and the config entry.

    Test, for each platform, that the device was linked to the
    config entry and the link was removed when the device is
    changed in the integration options.
    """

    def check_template_entities(
        template_entity_id: str,
        device_id: str | None = None,
    ) -> None:
        """Check that the template entity is linked to the correct device."""
        template_entity_ids: list[str] = []
        for template_entity in entity_registry.entities.get_entries_for_config_entry_id(
            template_config_entry.entry_id
        ):
            template_entity_ids.append(template_entity.entity_id)
            assert template_entity.device_id == device_id
        assert template_entity_ids == [template_entity_id]

    # Configure devices registry
    entry_device1 = MockConfigEntry()
    entry_device1.add_to_hass(hass)
    device1 = device_registry.async_get_or_create(
        config_entry_id=entry_device1.entry_id,
        identifiers={("test", "identifier_test1")},
        connections={("mac", "20:31:32:33:34:01")},
    )
    entry_device2 = MockConfigEntry()
    entry_device2.add_to_hass(hass)
    device2 = device_registry.async_get_or_create(
        config_entry_id=entry_device1.entry_id,
        identifiers={("test", "identifier_test2")},
        connections={("mac", "20:31:32:33:34:02")},
    )
    await hass.async_block_till_done()

    device_id1 = device1.id
    assert device_id1 is not None

    device_id2 = device2.id
    assert device_id2 is not None

    # Setup the config entry
    template_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options=config_entry_options | {"device_id": device_id1},
        title="Template",
    )
    template_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(template_config_entry.entry_id)
    await hass.async_block_till_done()

    template_entity_id = f"{config_entry_options['template_type']}.my_template"

    # Confirm that the template config entry has not been added to either device
    # and that the entities are linked to device 1
    for device_id in (device_id1, device_id2):
        device = device_registry.async_get(device_id=device_id)
        assert template_config_entry.entry_id not in device.config_entries
    check_template_entities(template_entity_id, device_id1)

    # Change config options to use device 2 and reload the integration
    result = await hass.config_entries.options.async_init(
        template_config_entry.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=config_user_input | {"device_id": device_id2},
    )
    await hass.async_block_till_done()

    # Confirm that the template config entry has not been added to either device
    # and that the entities are linked to device 2
    for device_id in (device_id1, device_id2):
        device = device_registry.async_get(device_id=device_id)
        assert template_config_entry.entry_id not in device.config_entries
    check_template_entities(template_entity_id, device_id2)

    # Change the config options to remove the device and reload the integration
    result = await hass.config_entries.options.async_init(
        template_config_entry.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=config_user_input,
    )
    await hass.async_block_till_done()

    # Confirm that the template config entry has not been added to either device
    # and that the entities are not linked to any device
    for device_id in (device_id1, device_id2):
        device = device_registry.async_get(device_id=device_id)
        assert template_config_entry.entry_id not in device.config_entries
    check_template_entities(template_entity_id, None)

    # Confirm that there is no device with the helper config entry
    assert (
        dr.async_entries_for_config_entry(
            device_registry, template_config_entry.entry_id
        )
        == []
    )