async def test_migration_from_v2_1(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    device_changes: dict[str, str],
    extra_subentries: list[ConfigSubentryData],
    expected_device_subentries: dict[str, set[str | None]],
) -> None:
    """Test migration from version 2.1.

    This tests we clean up the broken migration in Home Assistant Core
    2025.7.0b0-2025.7.0b1 and add AI Task and STT subentries:
    - Fix device registry (Fixed in Home Assistant Core 2025.7.0b2)
    - Add TTS subentry (Added in Home Assistant Core 2025.7.0b1)
    - Add AI Task subentry (Added in version 2.3)
    - Add STT subentry (Added in version 2.3)
    """
    # Create a v2.1 config entry with 2 subentries, devices and entities
    options = {
        "recommended": True,
        "llm_hass_api": ["assist"],
        "prompt": "You are a helpful assistant",
        "chat_model": "models/gemini-2.0-flash",
    }
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "1234"},
        entry_id="mock_entry_id",
        version=2,
        minor_version=1,
        subentries_data=[
            ConfigSubentryData(
                data=options,
                subentry_id="mock_id_1",
                subentry_type="conversation",
                title="Google Generative AI",
                unique_id=None,
            ),
            ConfigSubentryData(
                data=options,
                subentry_id="mock_id_2",
                subentry_type="conversation",
                title="Google Generative AI 2",
                unique_id=None,
            ),
            *extra_subentries,
        ],
        title="Google Generative AI",
    )
    mock_config_entry.add_to_hass(hass)

    device_1 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        config_subentry_id="mock_id_1",
        identifiers={(DOMAIN, "mock_id_1")},
        name="Google Generative AI",
        manufacturer="Google",
        model="Generative AI",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    device_1 = device_registry.async_update_device(device_1.id, **device_changes)
    assert device_1.config_entries_subentries == expected_device_subentries
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        "mock_id_1",
        config_entry=mock_config_entry,
        config_subentry_id="mock_id_1",
        device_id=device_1.id,
        suggested_object_id="google_generative_ai_conversation",
    )

    device_2 = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        config_subentry_id="mock_id_2",
        identifiers={(DOMAIN, "mock_id_2")},
        name="Google Generative AI 2",
        manufacturer="Google",
        model="Generative AI",
        entry_type=dr.DeviceEntryType.SERVICE,
    )
    entity_registry.async_get_or_create(
        "conversation",
        DOMAIN,
        "mock_id_2",
        config_entry=mock_config_entry,
        config_subentry_id="mock_id_2",
        device_id=device_2.id,
        suggested_object_id="google_generative_ai_conversation_2",
    )

    # Run migration
    with patch(
        "homeassistant.components.google_generative_ai_conversation.async_setup_entry",
        return_value=True,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.version == 2
    assert entry.minor_version == 4
    assert not entry.options
    assert entry.title == DEFAULT_TITLE
    assert len(entry.subentries) == 5
    conversation_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "conversation"
    ]
    assert len(conversation_subentries) == 2
    for subentry in conversation_subentries:
        assert subentry.subentry_type == "conversation"
        assert subentry.data == options
        assert "Google Generative AI" in subentry.title
    tts_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "tts"
    ]
    assert len(tts_subentries) == 1
    assert tts_subentries[0].data == RECOMMENDED_TTS_OPTIONS
    assert tts_subentries[0].title == DEFAULT_TTS_NAME
    ai_task_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "ai_task_data"
    ]
    assert len(ai_task_subentries) == 1
    assert ai_task_subentries[0].data == RECOMMENDED_AI_TASK_OPTIONS
    assert ai_task_subentries[0].title == DEFAULT_AI_TASK_NAME
    stt_subentries = [
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "stt"
    ]
    assert len(stt_subentries) == 1
    assert stt_subentries[0].data == RECOMMENDED_STT_OPTIONS
    assert stt_subentries[0].title == DEFAULT_STT_NAME

    subentry = conversation_subentries[0]

    entity = entity_registry.async_get("conversation.google_generative_ai_conversation")
    assert entity.unique_id == subentry.subentry_id
    assert entity.config_subentry_id == subentry.subentry_id
    assert entity.config_entry_id == entry.entry_id

    assert not device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry.entry_id)}
    )
    assert (
        device := device_registry.async_get_device(
            identifiers={(DOMAIN, subentry.subentry_id)}
        )
    )
    assert device.identifiers == {(DOMAIN, subentry.subentry_id)}
    assert device.id == device_1.id
    assert device.config_entries == {mock_config_entry.entry_id}
    assert device.config_entries_subentries == {
        mock_config_entry.entry_id: {subentry.subentry_id}
    }

    subentry = conversation_subentries[1]

    entity = entity_registry.async_get(
        "conversation.google_generative_ai_conversation_2"
    )
    assert entity.unique_id == subentry.subentry_id
    assert entity.config_subentry_id == subentry.subentry_id
    assert entity.config_entry_id == entry.entry_id
    assert not device_registry.async_get_device(
        identifiers={(DOMAIN, mock_config_entry.entry_id)}
    )
    assert (
        device := device_registry.async_get_device(
            identifiers={(DOMAIN, subentry.subentry_id)}
        )
    )
    assert device.identifiers == {(DOMAIN, subentry.subentry_id)}
    assert device.id == device_2.id
    assert device.config_entries == {mock_config_entry.entry_id}
    assert device.config_entries_subentries == {
        mock_config_entry.entry_id: {subentry.subentry_id}
    }