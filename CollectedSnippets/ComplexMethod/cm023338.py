async def test_ssdp_update_seen_bootid(
    hass: HomeAssistant,
    domain_data_mock: Mock,
    ssdp_scanner_mock: Mock,
    mock_disconnected_entity_id: str,
    dmr_device_mock: Mock,
) -> None:
    """Test device does not reconnect when it gets ssdp:update with next bootid."""
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

    # Send SSDP update with next boot ID
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={
                "NTS": "ssdp:update",
                ssdp.ATTR_SSDP_BOOTID: "1",
                ssdp.ATTR_SSDP_NEXTBOOTID: "2",
            },
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.UPDATE,
    )
    await hass.async_block_till_done()

    # Device was not reconnected, even with a new boot ID
    mock_state = hass.states.get(entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE

    assert dmr_device_mock.async_unsubscribe_services.await_count == 0
    assert dmr_device_mock.async_subscribe_services.await_count == 1

    # Send SSDP update with same next boot ID, again
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={
                "NTS": "ssdp:update",
                ssdp.ATTR_SSDP_BOOTID: "1",
                ssdp.ATTR_SSDP_NEXTBOOTID: "2",
            },
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.UPDATE,
    )
    await hass.async_block_till_done()

    # Nothing should change
    mock_state = hass.states.get(entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE

    assert dmr_device_mock.async_unsubscribe_services.await_count == 0
    assert dmr_device_mock.async_subscribe_services.await_count == 1

    # Send SSDP update with bad next boot ID
    await ssdp_callback(
        SsdpServiceInfo(
            ssdp_usn=MOCK_DEVICE_USN,
            ssdp_udn=MOCK_DEVICE_UDN,
            ssdp_headers={
                "NTS": "ssdp:update",
                ssdp.ATTR_SSDP_BOOTID: "2",
                ssdp.ATTR_SSDP_NEXTBOOTID: "7c848375-a106-4bd1-ac3c-8e50427c8e4f",
            },
            ssdp_st=MOCK_DEVICE_TYPE,
            upnp={},
        ),
        ssdp.SsdpChange.UPDATE,
    )
    await hass.async_block_till_done()

    # Nothing should change
    mock_state = hass.states.get(entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE

    assert dmr_device_mock.async_unsubscribe_services.await_count == 0
    assert dmr_device_mock.async_subscribe_services.await_count == 1

    # Send a new SSDP alive with the new boot ID, device should not reconnect
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

    assert dmr_device_mock.async_unsubscribe_services.await_count == 0
    assert dmr_device_mock.async_subscribe_services.await_count == 1