async def mock_entity_id(
    hass: HomeAssistant,
    domain_data_mock: Mock,
    config_entry_mock: MockConfigEntry,
    ssdp_scanner_mock: Mock,
    dmr_device_mock: Mock,
) -> AsyncGenerator[str]:
    """Fixture to set up a mock DlnaDmrEntity in a connected state.

    Yields the entity ID. Cleans up the entity after the test is complete.
    """
    config_entry_mock.add_to_hass(hass)
    entity_id = await setup_mock_component(hass, config_entry_mock)

    # Check the entity has registered all needed listeners
    assert len(config_entry_mock.update_listeners) == 1
    assert domain_data_mock.async_get_event_notifier.await_count == 1
    assert domain_data_mock.async_release_event_notifier.await_count == 0
    assert ssdp_scanner_mock.async_register_callback.await_count == 2
    assert ssdp_scanner_mock.async_register_callback.return_value.call_count == 0
    assert dmr_device_mock.async_subscribe_services.await_count == 1
    assert dmr_device_mock.async_unsubscribe_services.await_count == 0
    assert dmr_device_mock.on_event is not None

    # Run the test
    yield entity_id

    # Unload config entry to clean up
    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }

    # Check entity has cleaned up its resources
    assert not config_entry_mock.update_listeners
    assert (
        domain_data_mock.async_get_event_notifier.await_count
        == domain_data_mock.async_release_event_notifier.await_count
    )
    assert (
        ssdp_scanner_mock.async_register_callback.await_count
        == ssdp_scanner_mock.async_register_callback.return_value.call_count
    )
    assert (
        dmr_device_mock.async_subscribe_services.await_count
        == dmr_device_mock.async_unsubscribe_services.await_count
    )
    assert dmr_device_mock.on_event is None