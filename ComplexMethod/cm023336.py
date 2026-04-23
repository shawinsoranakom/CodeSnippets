async def test_become_available(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    domain_data_mock: Mock,
    ssdp_scanner_mock: Mock,
    config_entry_mock: MockConfigEntry,
    dmr_device_mock: Mock,
    core_state: CoreState,
) -> None:
    """Test a device becoming available after the entity is constructed."""
    # Cause connection attempts to fail before adding entity
    hass.set_state(core_state)
    domain_data_mock.upnp_factory.async_create_device.side_effect = UpnpConnectionError
    config_entry_mock.add_to_hass(hass)
    mock_entity_id = await setup_mock_component(hass, config_entry_mock)
    mock_state = hass.states.get(mock_entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE

    # Check hass device information has not been filled in yet
    device = device_registry.async_get_device(
        connections={(dr.CONNECTION_UPNP, MOCK_DEVICE_UDN)},
        identifiers=set(),
    )
    assert device is not None

    # Mock device is now available.
    domain_data_mock.upnp_factory.async_create_device.side_effect = None
    domain_data_mock.upnp_factory.async_create_device.reset_mock()

    # Send an SSDP notification from the now alive device
    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    # Check device was created from the supplied URL
    domain_data_mock.upnp_factory.async_create_device.assert_awaited_once_with(
        NEW_DEVICE_LOCATION
    )
    # Check event notifiers are acquired
    domain_data_mock.async_get_event_notifier.assert_awaited_once_with(
        EventListenAddr(LOCAL_IP, 0, None), hass
    )
    # Check UPnP services are subscribed
    dmr_device_mock.async_subscribe_services.assert_awaited_once_with(
        auto_resubscribe=True
    )
    assert dmr_device_mock.on_event is not None
    # Quick check of the state to verify the entity has a connected DmrDevice
    mock_state = hass.states.get(mock_entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE
    # Check hass device information is now filled in
    device = device_registry.async_get_device(
        connections={(dr.CONNECTION_UPNP, MOCK_DEVICE_UDN)},
        identifiers=set(),
    )
    assert device is not None
    assert device.manufacturer == "device_manufacturer"
    assert device.model == "device_model_name"
    assert device.name == "device_name"

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