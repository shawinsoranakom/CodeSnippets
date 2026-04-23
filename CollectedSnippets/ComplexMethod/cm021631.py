async def test_config_flow_entry_migrate(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that config flow entry is migrated correctly."""
    # Start with the config entry at Version 1.
    manager = hass.config_entries
    mock_entry = MOCK_ENTRY_VERSION_1
    mock_entry.add_to_manager(manager)
    mock_device_entry = device_registry.async_get_or_create(
        config_entry_id=mock_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    mock_entity_id = f"media_player.ps4_{MOCK_UNIQUE_ID}"
    mock_e_entry = entity_registry.async_get_or_create(
        "media_player",
        "ps4",
        MOCK_UNIQUE_ID,
        config_entry=mock_entry,
        device_id=mock_device_entry.id,
    )
    assert len(entity_registry.entities) == 1
    assert mock_e_entry.entity_id == mock_entity_id
    assert mock_e_entry.unique_id == MOCK_UNIQUE_ID

    with (
        patch(
            "homeassistant.util.location.async_detect_location_info",
            return_value=MOCK_LOCATION,
        ),
        patch(
            "homeassistant.helpers.entity_registry.async_get",
            return_value=entity_registry,
        ),
    ):
        await ps4.async_migrate_entry(hass, mock_entry)

    await hass.async_block_till_done()

    assert len(entity_registry.entities) == 1
    for entity in entity_registry.entities.values():
        mock_entity = entity

    # Test that entity_id remains the same.
    assert mock_entity.entity_id == mock_entity_id
    assert mock_entity.device_id == mock_device_entry.id

    # Test that last four of credentials is appended to the unique_id.
    assert mock_entity.unique_id == f"{MOCK_UNIQUE_ID}_{MOCK_CREDS[-4:]}"

    # Test that config entry is at the current version.
    assert mock_entry.version == VERSION
    assert mock_entry.data[CONF_TOKEN] == MOCK_CREDS
    assert mock_entry.data["devices"][0][CONF_HOST] == MOCK_HOST
    assert mock_entry.data["devices"][0][CONF_NAME] == MOCK_NAME
    assert mock_entry.data["devices"][0][CONF_REGION] == DEFAULT_REGION