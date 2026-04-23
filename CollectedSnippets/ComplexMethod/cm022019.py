async def test_registry_cleanup_multiple_entries(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Ensure multiple config entries do not remove items from other entries."""
    main_entity_id = "sensor.boite_aux_lettres_arriere_battery"
    second_entity_id = "binary_sensor.window_downstairs_door"

    main_manager = create_manager()
    main_device = await create_device(hass, "mcs_8yhypbo7")
    await initialize_entry(hass, main_manager, mock_config_entry, main_device)

    # Ensure initial setup is correct (main present, second absent)
    assert hass.states.get(main_entity_id)
    assert entity_registry.async_get(main_entity_id)
    assert not hass.states.get(second_entity_id)
    assert not entity_registry.async_get(second_entity_id)

    # Create a second config entry
    second_config_entry = MockConfigEntry(
        title="Test Tuya entry",
        domain=DOMAIN,
        data={
            CONF_ENDPOINT: "test_endpoint",
            CONF_TERMINAL_ID: "test_terminal",
            CONF_TOKEN_INFO: "test_token",
            CONF_USER_CODE: "test_user_code",
        },
        unique_id="56789",
    )
    second_manager = create_manager()
    second_device = await create_device(hass, "mcs_oxslv1c9")
    await initialize_entry(hass, second_manager, second_config_entry, second_device)

    # Ensure setup is correct (both present)
    assert hass.states.get(main_entity_id)
    assert entity_registry.async_get(main_entity_id)
    assert hass.states.get(second_entity_id)
    assert entity_registry.async_get(second_entity_id)