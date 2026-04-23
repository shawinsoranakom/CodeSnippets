async def test_migration_from_v1_with_multiple_urls(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test migration from version 1 with different URLs."""
    # Create two v1 config entries with different URLs
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"url": "http://localhost:11434", "model": "llama3.2:latest"},
        options=V1_TEST_OPTIONS,
        version=1,
        title="Ollama 1",
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry_2 = MockConfigEntry(
        domain=DOMAIN,
        data={"url": "http://localhost:11435", "model": "llama3.2:latest"},
        options=V1_TEST_OPTIONS,
        version=1,
        title="Ollama 2",
    )
    mock_config_entry_2.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, mock_config_entry.entry_id)},
        name=mock_config_entry.title,
        manufacturer="Ollama",
        model="Ollama 1",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry.entry_id,
        config_entry=mock_config_entry,
        device_id=device.id,
        suggested_object_id="ollama_1",
    )

    device_2 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry_2.entry_id,
        identifiers={(DOMAIN, mock_config_entry_2.entry_id)},
        name=mock_config_entry_2.title,
        manufacturer="Ollama",
        model="Ollama 2",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        mock_config_entry_2.entry_id,
        config_entry=mock_config_entry_2,
        device_id=device_2.id,
        suggested_object_id="ollama_2",
    )

    # Run migration
    with patch(
        "homeassistant.components.ollama.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 2

    for idx, entry in enumerate(entries):
        assert entry.version == 3
        assert entry.minor_version == 3
        assert not entry.options
        assert len(entry.subentries) == 2

        subentry = next(
            iter(
                subentry
                for subentry in entry.subentries.values()
                if subentry.subentry_type == "conversation"
            )
        )
        assert subentry.subentry_type == "conversation"
        # Subentry should include the model along with the original options
        expected_subentry_data = TEST_OPTIONS.copy()
        expected_subentry_data["model"] = "llama3.2:latest"
        assert subentry.data == expected_subentry_data
        assert subentry.title == f"Ollama {idx + 1}"

        # Find the AI Task subentry
        ai_task_subentry = next(
            iter(
                subentry
                for subentry in entry.subentries.values()
                if subentry.subentry_type == "ai_task_data"
            )
        )
        assert ai_task_subentry.subentry_type == "ai_task_data"
        assert ai_task_subentry.title == "Ollama AI Task"

        dev = device_registry.async_get_device(
            identifiers={(DOMAIN, list(entry.subentries.values())[0].subentry_id)}
        )
        assert dev is not None
        assert dev.config_entries == {entry.entry_id}
        assert dev.config_entries_subentries == {entry.entry_id: {subentry.subentry_id}}