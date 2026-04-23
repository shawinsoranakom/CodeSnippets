async def test_poll_availability(
    hass: HomeAssistant,
    domain_data_mock: Mock,
    config_entry_mock: MockConfigEntry,
    dmr_device_mock: Mock,
) -> None:
    """Test device becomes available and noticed via poll_availability."""
    # Start with a disconnected device and poll_availability=True
    domain_data_mock.upnp_factory.async_create_device.side_effect = UpnpConnectionError
    config_entry_mock.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        config_entry_mock,
        options={
            CONF_POLL_AVAILABILITY: True,
        },
    )
    mock_entity_id = await setup_mock_component(hass, config_entry_mock)
    mock_state = hass.states.get(mock_entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE

    # Check that an update will poll the device for availability
    domain_data_mock.upnp_factory.async_create_device.reset_mock()
    await async_update_entity(hass, mock_entity_id)
    await hass.async_block_till_done()

    domain_data_mock.upnp_factory.async_create_device.assert_awaited_once_with(
        MOCK_DEVICE_LOCATION
    )

    mock_state = hass.states.get(mock_entity_id)
    assert mock_state is not None
    assert mock_state.state == ha_const.STATE_UNAVAILABLE

    # "Reconnect" the device
    domain_data_mock.upnp_factory.async_create_device.side_effect = None

    # Check that an update will notice the device and connect to it
    domain_data_mock.upnp_factory.async_create_device.reset_mock()
    await async_update_entity(hass, mock_entity_id)
    await hass.async_block_till_done()

    domain_data_mock.upnp_factory.async_create_device.assert_awaited_once_with(
        MOCK_DEVICE_LOCATION
    )

    mock_state = hass.states.get(mock_entity_id)
    assert mock_state is not None
    assert mock_state.state == MediaPlayerState.IDLE

    # Clean up
    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }