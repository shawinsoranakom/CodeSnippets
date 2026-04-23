async def test_available_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    dmr_device_mock: Mock,
    mock_entity_id: str,
) -> None:
    """Test a DlnaDmrEntity with a connected DmrDevice."""
    # Check hass device information is filled in
    await async_update_entity(hass, mock_entity_id)
    await hass.async_block_till_done()
    device = device_registry.async_get_device(
        connections={(dr.CONNECTION_UPNP, MOCK_DEVICE_UDN)},
        identifiers=set(),
    )
    assert device is not None
    # Device properties are set in dmr_device_mock before the entity gets constructed
    assert device.manufacturer == "device_manufacturer"
    assert device.model == "device_model_name"
    assert device.name == "device_name"

    # Check entity state gets updated when device changes state
    for dev_state, ent_state in (
        (None, MediaPlayerState.ON),
        (TransportState.STOPPED, MediaPlayerState.IDLE),
        (TransportState.PLAYING, MediaPlayerState.PLAYING),
        (TransportState.TRANSITIONING, MediaPlayerState.PLAYING),
        (TransportState.PAUSED_PLAYBACK, MediaPlayerState.PAUSED),
        (TransportState.PAUSED_RECORDING, MediaPlayerState.PAUSED),
        (TransportState.RECORDING, MediaPlayerState.IDLE),
        (TransportState.NO_MEDIA_PRESENT, MediaPlayerState.IDLE),
        (TransportState.VENDOR_DEFINED, ha_const.STATE_UNKNOWN),
    ):
        dmr_device_mock.profile_device.available = True
        dmr_device_mock.transport_state = dev_state
        await async_update_entity(hass, mock_entity_id)
        entity_state = hass.states.get(mock_entity_id)
        assert entity_state is not None
        assert entity_state.state == ent_state

    dmr_device_mock.profile_device.available = False
    dmr_device_mock.transport_state = TransportState.PLAYING
    await async_update_entity(hass, mock_entity_id)
    entity_state = hass.states.get(mock_entity_id)
    assert entity_state is not None
    assert entity_state.state == ha_const.STATE_UNAVAILABLE