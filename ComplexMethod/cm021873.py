async def test_hmip_multi_switch(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipMultiSwitch."""
    entity_id = "switch.jalousien_1_kizi_2_schlazi_channel1"
    entity_name = "Jalousien - 1 KiZi, 2 SchlaZi Channel1"
    device_model = "HmIP-PCBS2"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[
            "Jalousien - 1 KiZi, 2 SchlaZi",
            "Multi IO Box",
            "Heizungsaktor",
            "ioBroker",
            "Schaltaktor Verteiler",
        ]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_OFF
    service_call_counter = len(hmip_device.functionalChannels[1].mock_calls)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 1
    assert hmip_device.functionalChannels[1].mock_calls[-1][0] == "async_turn_on"
    assert hmip_device.functionalChannels[1].mock_calls[-1][1] == ()
    await async_manipulate_test_data(hass, hmip_device, "on", True)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_ON

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.functionalChannels[1].mock_calls) == service_call_counter + 2
    assert hmip_device.functionalChannels[1].mock_calls[-1][0] == "async_turn_off"
    assert hmip_device.functionalChannels[1].mock_calls[-1][1] == ()
    await async_manipulate_test_data(hass, hmip_device, "on", False)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_OFF

    ha_state, hmip_device = get_and_check_entity_basics(
        hass,
        mock_hap,
        "switch.schaltaktor_verteiler_channel3",
        "Schaltaktor Verteiler Channel3",
        "HmIP-DRSI4",
    )

    assert ha_state.state == STATE_OFF