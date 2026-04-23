async def test_migration_from_v1_disabled(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    config_entry_disabled_by: list[ConfigEntryDisabler | None],
    device_disabled_by: list[DeviceEntryDisabler | None],
    entity_disabled_by: list[RegistryEntryDisabler | None],
    merged_config_entry_disabled_by: ConfigEntryDisabler | None,
    conversation_subentry_data: list[dict[str, Any]],
    main_config_entry: int,
) -> None:
    """Test migration where the config entries are disabled."""
    # Create a v1 config entry with conversation options and an entity
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"url": "http://localhost:11434", "model": "llama3.2:latest"},
        options=V1_TEST_OPTIONS,
        version=1,
        title="Ollama",
        disabled_by=config_entry_disabled_by[0],
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry_2 = MockConfigEntry(
        domain=DOMAIN,
        data={"url": "http://localhost:11434", "model": "llama3.2:latest"},
        options=V1_TEST_OPTIONS,
        version=1,
        title="Ollama 2",
        disabled_by=config_entry_disabled_by[1],
    )
    mock_config_entry_2.add_to_hass(hass)
    mock_config_entries = [mock_config_entry, mock_config_entry_2]

    device_1 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, mock_config_entry.entry_id)},
        name=mock_config_entry.title,
        manufacturer="Ollama",
        model="Ollama",
        entry_type=dr.DeviceEntryType.SERVICE,
        disabled_by=device_disabled_by[0],
    )
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry.entry_id,
        config_entry=mock_config_entry,
        device_id=device_1.id,
        suggested_object_id="ollama",
        disabled_by=entity_disabled_by[0],
    )

    device_2 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_2.entry_id,
        identifiers={(DOMAIN, mock_config_entry_2.entry_id)},
        name=mock_config_entry_2.title,
        manufacturer="Ollama",
        model="Ollama",
        entry_type=dr.DeviceEntryType.SERVICE,
        disabled_by=device_disabled_by[1],
    )
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry_2.entry_id,
        config_entry=mock_config_entry_2,
        device_id=device_2.id,
        suggested_object_id="ollama_2",
        disabled_by=entity_disabled_by[1],
    )

    devices = [device_1, device_2]

    # Run migration
    with patch(
        "homeassistant.components.ollama.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.disabled_by is merged_config_entry_disabled_by
    assert entry.version == 3
    assert entry.minor_version == 3
    assert not entry.options
    assert entry.title == "Ollama"
    assert len(entry.subentries) == 3
    conversation_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "conversation"
    ]
    assert len(conversation_subentries) == 2
    for subentry in conversation_subentries:
        assert subentry.subentry_type == "conversation"
        assert subentry.data == {"model": "llama3.2:latest", **V1_TEST_OPTIONS}
        assert "Ollama" in subentry.title
    ai_task_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "ai_task_data"
    ]
    assert len(ai_task_subentries) == 1
    assert ai_task_subentries[0].data == {"model": "llama3.2:latest"}
    assert ai_task_subentries[0].title == "Ollama AI Task"

    assert not device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry.entry_id)}
    )
    assert not device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry_2.entry_id)}
    )

    for idx, subentry in enumerate(conversation_subentries):
        subentry_data = conversation_subentry_data[idx]
        entity = entity_registry.async_get(subentry_data["conversation_entity_id"])
        assert entity.unique_id == subentry.subentry_id
        assert entity.config_subentry_id == subentry.subentry_id
        assert entity.config_entry_id == entry.entry_id
        assert entity.disabled_by is subentry_data["entity_disabled_by"]

        assert (
            device := device_registry.async_get_device(
                identifiers={(DOMAIN, subentry.subentry_id)}
            )
        )
        assert device.identifiers == {(DOMAIN, subentry.subentry_id)}
        assert device.id == devices[subentry_data["device"]].id
        assert device.config_entries == {
            mock_config_entries[main_config_entry].entry_id
        }
        assert device.config_entries_subentries == {
            mock_config_entries[main_config_entry].entry_id: {subentry.subentry_id}
        }
        assert device.disabled_by is subentry_data["device_disabled_by"]