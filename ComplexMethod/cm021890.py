async def test_hmip_garage_door_hoermann(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipCoverShutte."""
    entity_id = "cover.garage_door"
    entity_name = "Garage door"
    device_model = "HmIP-MOD-HO"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "closed"
    assert ha_state.attributes["current_position"] == 0
    service_call_counter = len(hmip_device.functionalChannels[1].mock_calls)

    await hass.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 1
    assert (
        hmip_device.functionalChannels[1].mock_calls[-1][0] == "async_send_door_command"
    )
    assert hmip_device.functionalChannels[1].mock_calls[-1][1] == (DoorCommand.OPEN,)
    await async_manipulate_test_data(hass, hmip_device, "doorState", DoorState.OPEN)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100

    await hass.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 2
    assert (
        hmip_device.functionalChannels[1].mock_calls[-1][0] == "async_send_door_command"
    )
    assert hmip_device.functionalChannels[1].mock_calls[-1][1] == (DoorCommand.CLOSE,)
    await async_manipulate_test_data(hass, hmip_device, "doorState", DoorState.CLOSED)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0

    await hass.services.async_call(
        "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 3
    assert (
        hmip_device.functionalChannels[1].mock_calls[-1][0] == "async_send_door_command"
    )
    assert hmip_device.functionalChannels[1].mock_calls[-1][1] == (DoorCommand.STOP,)