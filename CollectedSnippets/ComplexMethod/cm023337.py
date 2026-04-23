async def test_alive_but_gone(
    hass: HomeAssistant,
    domain_data_mock: Mock,
    ssdp_scanner_mock: Mock,
    mock_disconnected_entity_id: str,
    core_state: CoreState,
) -> None:
    """Test a device sending an SSDP alive announcement, but not being connectable."""
    hass.set_state(core_state)
    domain_data_mock.upnp_factory.async_create_device.side_effect = UpnpError

    # Send an SSDP notification from the still missing device
    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    # There should be a connection attempt to the device
    domain_data_mock.upnp_factory.async_create_device.assert_awaited()

    # Device should still be unavailable
    mock_state = hass.states.get(mock_disconnected_entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE

    # Send the same SSDP notification, expecting no extra connection attempts
    domain_data_mock.upnp_factory.async_create_device.reset_mock()
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()
    domain_data_mock.upnp_factory.async_create_device.assert_not_called()
    domain_data_mock.upnp_factory.async_create_device.assert_not_awaited()
    mock_state = hass.states.get(mock_disconnected_entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE

    # Send an SSDP notification with a new BOOTID, indicating the device has rebooted
    domain_data_mock.upnp_factory.async_create_device.reset_mock()
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "2"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    # Rebooted device (seen via BOOTID) should mean a new connection attempt
    domain_data_mock.upnp_factory.async_create_device.assert_awaited()
    mock_state = hass.states.get(mock_disconnected_entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE

    # Send byebye message to indicate device is going away. Next alive message
    # should result in a reconnect attempt even with same BOOTID.
    domain_data_mock.upnp_factory.async_create_device.reset_mock()
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.BYEBYE,
    )
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=NEW_DEVICE_LOCATION,
            ssdp_st=MOCK_DEVICE_TYPE,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "2"},
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    # Rebooted device (seen via byebye/alive) should mean a new connection attempt
    domain_data_mock.upnp_factory.async_create_device.assert_awaited()
    mock_state = hass.states.get(mock_disconnected_entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE