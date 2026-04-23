async def test_ssdp_bootid(
    hass: HomeAssistant,
    domain_data_mock: Mock,
    ssdp_scanner_mock: Mock,
    mock_disconnected_entity_id: str,
    dmr_device_mock: Mock,
) -> None:
    """Test an alive with a new BOOTID.UPNP.ORG header causes a reconnect."""
    # Start with a disconnected device
    entity_id = mock_disconnected_entity_id
    mock_state = hass.states.get(entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE

    # "Reconnect" the device
    domain_data_mock.upnp_factory.async_create_device.side_effect = None

    # Send SSDP alive with boot ID
    ssdp_callback = ssdp_scanner_mock.async_register_callback.call_args.args[0].target
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    mock_state = hass.states.get(entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE

    assert dmr_device_mock.async_subscribe_services.call_count == 1
    assert dmr_device_mock.async_unsubscribe_services.call_count == 0

    # Send SSDP alive with same boot ID, nothing should happen
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "1"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    mock_state = hass.states.get(entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE

    assert dmr_device_mock.async_subscribe_services.call_count == 1
    assert dmr_device_mock.async_unsubscribe_services.call_count == 0

    # Send a new SSDP alive with an incremented boot ID, device should be dis/reconnected
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_location=MOCK_DEVICE_LOCATION,
            ssdp_headers={ssdp.ATTR_SSDP_BOOTID: "2"},
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.ALIVE,
    )
    await hass.async_block_till_done()

    mock_state = hass.states.get(entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE

    assert dmr_device_mock.async_subscribe_services.call_count == 2
    assert dmr_device_mock.async_unsubscribe_services.call_count == 1