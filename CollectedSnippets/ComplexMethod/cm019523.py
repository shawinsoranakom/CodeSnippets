async def test_update_unique_id_camera_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
    mock_ring_client,
) -> None:
    """Test camera unique id with no suffix is updated."""
    correct_unique_id = "123456-last_recording"
    entry = MockConfigEntry(
        title="Ring",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "foo@bar.com",
            "token": {"access_token": "mock-token"},
        },
        unique_id="foo@bar.com",
        minor_version=1,
    )
    entry.add_to_hass(hass)

    entity = entity_registry.async_get_or_create(
        domain=CAMERA_DOMAIN,
        platform=DOMAIN,
        unique_id="123456",
        config_entry=entry,
    )
    assert entity.unique_id == "123456"
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_migrated = entity_registry.async_get(entity.entity_id)
    assert entity_migrated
    assert entity_migrated.unique_id == correct_unique_id
    assert entity.disabled is False
    assert "Fixing non string unique id" not in caplog.text
    assert entry.minor_version == CONF_CONFIG_ENTRY_MINOR_VERSION