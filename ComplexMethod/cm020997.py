async def test_entry_migration(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    v1_mock_config_entry: MockConfigEntry,
) -> None:
    """Test entry migration from version 1 to 3, where host and port is required for the connection to the server."""
    v1_mock_config_entry.add_to_hass(hass)

    device_entry_id = create_v1_mock_device_entry(hass, v1_mock_config_entry.entry_id)
    sensor_entity_id_key_mapping_list = create_v1_mock_sensor_entity_entries(
        hass, v1_mock_config_entry.entry_id, device_entry_id
    )
    binary_sensor_entity_id_key_mapping = create_v1_mock_binary_sensor_entity_entry(
        hass, v1_mock_config_entry.entry_id, device_entry_id
    )

    # Trigger migration.
    with (
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_lookup",
            side_effect=[
                ValueError,  # async_migrate_entry
                JavaServer(host=TEST_HOST, port=TEST_PORT),  # async_migrate_entry
                JavaServer(host=TEST_HOST, port=TEST_PORT),  # async_setup_entry
            ],
        ),
        patch(
            "homeassistant.components.minecraft_server.api.JavaServer.async_status",
            return_value=TEST_JAVA_STATUS_RESPONSE,
        ),
    ):
        assert await hass.config_entries.async_setup(v1_mock_config_entry.entry_id)
        await hass.async_block_till_done()

    migrated_config_entry = v1_mock_config_entry

    # Test migrated config entry.
    assert migrated_config_entry.unique_id is None
    assert migrated_config_entry.data == {
        CONF_NAME: DEFAULT_NAME,
        CONF_ADDRESS: TEST_ADDRESS,
    }
    assert migrated_config_entry.version == 3
    assert migrated_config_entry.state is ConfigEntryState.LOADED

    # Test migrated device entry.
    device_entry = device_registry.async_get(device_entry_id)
    assert device_entry.identifiers == {(DOMAIN, migrated_config_entry.entry_id)}

    # Test migrated sensor entity entries.
    for mapping in sensor_entity_id_key_mapping_list:
        entity_entry = entity_registry.async_get(mapping["entity_id"])
        assert (
            entity_entry.unique_id
            == f"{migrated_config_entry.entry_id}-{mapping['key']}"
        )

    # Test migrated binary sensor entity entry.
    entity_entry = entity_registry.async_get(
        binary_sensor_entity_id_key_mapping["entity_id"]
    )
    assert (
        entity_entry.unique_id
        == f"{migrated_config_entry.entry_id}-{binary_sensor_entity_id_key_mapping['key']}"
    )