async def test_unavailable_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    domain_data_mock: Mock,
    ssdp_scanner_mock: Mock,
    config_entry_mock: MockConfigEntry,
    core_state: CoreState,
) -> None:
    """Test a DlnaDmrEntity with out a connected DmrDevice."""
    # Cause connection attempts to fail
    hass.set_state(core_state)
    domain_data_mock.upnp_factory.async_create_device.side_effect = UpnpConnectionError
    config_entry_mock.add_to_hass(hass)

    with patch(
        "homeassistant.components.dlna_dmr.media_player.DmrDevice", autospec=True
    ) as dmr_device_constructor_mock:
        mock_entity_id = await setup_mock_component(hass, config_entry_mock)
        mock_state = hass.states.get(mock_entity_id)
        assert mock_state is not None

        # Check device is not created
        dmr_device_constructor_mock.assert_not_called()

    # Check attempt was made to create a device from the supplied URL
    domain_data_mock.upnp_factory.async_create_device.assert_awaited_once_with(
        MOCK_DEVICE_LOCATION
    )
    # Check event notifiers are not acquired
    domain_data_mock.async_get_event_notifier.assert_not_called()
    # Check SSDP notifications are registered
    ssdp_scanner_mock.async_register_callback.assert_any_call(
        ANY, {"USN": MOCK_DEVICE_USN}
    )
    ssdp_scanner_mock.async_register_callback.assert_any_call(
        ANY, {"_udn": MOCK_DEVICE_UDN, "NTS": "ssdp:byebye"}
    )
    # Quick check of the state to verify the entity has no connected DmrDevice
    assert mock_state.state == ha_const.STATE_UNAVAILABLE
    # Check the name matches that supplied
    assert mock_state.name == MOCK_DEVICE_NAME

    # Check that an update does not attempt to contact the device because
    # poll_availability is False
    domain_data_mock.upnp_factory.async_create_device.reset_mock()
    await async_update_entity(hass, mock_entity_id)
    domain_data_mock.upnp_factory.async_create_device.assert_not_called()

    # Now set poll_availability = True and expect construction attempt
    hass.config_entries.async_update_entry(
        config_entry_mock, options={CONF_POLL_AVAILABILITY: True}
    )
    await hass.async_block_till_done()
    await async_update_entity(hass, mock_entity_id)
    domain_data_mock.upnp_factory.async_create_device.assert_awaited_once_with(
        MOCK_DEVICE_LOCATION
    )

    # Check attributes are unavailable
    attrs = mock_state.attributes
    for attr in mp.ATTR_TO_PROPERTY:
        assert attr not in attrs

    assert attrs[ha_const.ATTR_FRIENDLY_NAME] == MOCK_DEVICE_NAME
    assert attrs[ha_const.ATTR_SUPPORTED_FEATURES] == 0
    assert mp.ATTR_SOUND_MODE_LIST not in attrs

    # Check service calls do nothing
    SERVICES: list[tuple[str, dict]] = [
        (ha_const.SERVICE_VOLUME_SET, {mp.ATTR_MEDIA_VOLUME_LEVEL: 0.80}),
        (ha_const.SERVICE_VOLUME_MUTE, {mp.ATTR_MEDIA_VOLUME_MUTED: True}),
        (ha_const.SERVICE_MEDIA_PAUSE, {}),
        (ha_const.SERVICE_MEDIA_PLAY, {}),
        (ha_const.SERVICE_MEDIA_STOP, {}),
        (ha_const.SERVICE_MEDIA_NEXT_TRACK, {}),
        (ha_const.SERVICE_MEDIA_PREVIOUS_TRACK, {}),
        (ha_const.SERVICE_MEDIA_SEEK, {mp.ATTR_MEDIA_SEEK_POSITION: 33}),
        (
            mp.SERVICE_PLAY_MEDIA,
            {
                mp.ATTR_MEDIA_CONTENT_TYPE: MediaType.MUSIC,
                mp.ATTR_MEDIA_CONTENT_ID: (
                    "http://198.51.100.20:8200/MediaItems/17621.mp3"
                ),
                mp.ATTR_MEDIA_ENQUEUE: False,
            },
        ),
        (mp.SERVICE_SELECT_SOUND_MODE, {mp.ATTR_SOUND_MODE: "Default"}),
        (ha_const.SERVICE_SHUFFLE_SET, {mp.ATTR_MEDIA_SHUFFLE: True}),
        (ha_const.SERVICE_REPEAT_SET, {mp.ATTR_MEDIA_REPEAT: "all"}),
    ]
    for service, data in SERVICES:
        await hass.services.async_call(
            mp.DOMAIN,
            service,
            {ATTR_ENTITY_ID: mock_entity_id, **data},
            blocking=True,
        )

    # Check hass device information has not been filled in yet
    device = device_registry.async_get_device(
        connections={(dr.CONNECTION_UPNP, MOCK_DEVICE_UDN)},
        identifiers=set(),
    )
    assert device is not None
    assert device.name is None
    assert device.manufacturer is None

    # Unload config entry to clean up
    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }

    # Confirm SSDP notifications unregistered
    assert ssdp_scanner_mock.async_register_callback.return_value.call_count == 2

    # Check event notifiers are not released
    domain_data_mock.async_release_event_notifier.assert_not_called()

    # Entity should be removed by the cleanup
    assert hass.states.get(mock_entity_id) is None