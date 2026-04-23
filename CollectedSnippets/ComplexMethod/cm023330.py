async def test_setup_entry_with_options(
    hass: HomeAssistant,
    domain_data_mock: Mock,
    ssdp_scanner_mock: Mock,
    config_entry_mock: MockConfigEntry,
    dmr_device_mock: Mock,
    core_state: CoreState,
) -> None:
    """Test setting options leads to a DlnaDmrEntity with custom event_handler.

    Check that the device is constructed properly as part of the test.
    """
    hass.set_state(core_state)
    config_entry_mock.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry_mock,
        options={
            CONF_LISTEN_PORT: 2222,
            CONF_CALLBACK_URL_OVERRIDE: "http://198.51.100.10/events",
            CONF_POLL_AVAILABILITY: True,
        },
    )
    mock_entity_id = await setup_mock_component(hass, config_entry_mock)
    await async_update_entity(hass, mock_entity_id)
    await hass.async_block_till_done()
    mock_state = hass.states.get(mock_entity_id)
    assert mock_state is not None

    # Check device was created from the supplied URL
    domain_data_mock.upnp_factory.async_create_device.assert_awaited_once_with(
        MOCK_DEVICE_LOCATION
    )
    # Check event notifiers are acquired with the configured port and callback URL
    domain_data_mock.async_get_event_notifier.assert_awaited_once_with(
        EventListenAddr(LOCAL_IP, 2222, "http://198.51.100.10/events"), hass
    )
    # Check UPnP services are subscribed
    dmr_device_mock.async_subscribe_services.assert_awaited_once_with(
        auto_resubscribe=True
    )
    assert dmr_device_mock.on_event is not None
    # Check SSDP notifications are registered
    ssdp_scanner_mock.async_register_callback.assert_any_call(
        ANY, {"USN": MOCK_DEVICE_USN}
    )
    ssdp_scanner_mock.async_register_callback.assert_any_call(
        ANY, {"_udn": MOCK_DEVICE_UDN, "NTS": "ssdp:byebye"}
    )
    # Quick check of the state to verify the entity has a connected DmrDevice
    assert mock_state.state == MediaPlayerState.IDLE
    # Check the name matches that supplied
    assert mock_state.name == MOCK_ENTITY_NAME

    # Check that an update retrieves state from the device, and also pings it,
    # because poll_availability is True
    await async_update_entity(hass, mock_entity_id)
    dmr_device_mock.async_update.assert_awaited_with(do_ping=True)

    # Unload config entry to clean up
    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }

    # Confirm SSDP notifications unregistered
    assert ssdp_scanner_mock.async_register_callback.return_value.call_count == 2

    # Confirm the entity has disconnected from the device
    domain_data_mock.async_release_event_notifier.assert_awaited_once()
    dmr_device_mock.async_unsubscribe_services.assert_awaited_once()
    assert dmr_device_mock.on_event is None
    # Entity should be removed by the cleanup
    assert hass.states.get(mock_entity_id) is None