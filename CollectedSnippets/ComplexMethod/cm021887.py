async def test_hmip_multi_cover_slats(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipCoverSlats."""
    entity_id = "cover.jalousieaktor_1_fur_hutschienenmontage_4_fach_wohnzimmer_fenster"
    entity_name = "Jalousieaktor 1 für Hutschienenmontage – 4-fach Wohnzimmer Fenster"
    device_model = "HmIP-DRBLI4"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Jalousieaktor 1 für Hutschienenmontage – 4-fach"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    await async_manipulate_test_data(hass, hmip_device, "shutterLevel", 1, channel=4)
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 1, channel=4)
    ha_state = hass.states.get(entity_id)

    assert ha_state.state == CoverState.CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await hass.services.async_call(
        "cover", "open_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_slats_level_async"
    assert hmip_device.mock_calls[-1][2] == {"channelIndex": 4, "slatsLevel": 0}
    await async_manipulate_test_data(hass, hmip_device, "shutterLevel", 0, channel=4)
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 0, channel=4)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    await hass.services.async_call(
        "cover",
        "set_cover_tilt_position",
        {"entity_id": entity_id, "tilt_position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 4
    assert hmip_device.mock_calls[-1][0] == "set_slats_level_async"
    assert hmip_device.mock_calls[-1][2] == {"channelIndex": 4, "slatsLevel": 0.5}
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 0.5, channel=4)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await hass.services.async_call(
        "cover", "close_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 6
    assert hmip_device.mock_calls[-1][0] == "set_slats_level_async"
    assert hmip_device.mock_calls[-1][2] == {"channelIndex": 4, "slatsLevel": 1}
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 1, channel=4)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await hass.services.async_call(
        "cover", "stop_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 8
    assert hmip_device.mock_calls[-1][0] == "set_shutter_stop_async"
    assert hmip_device.mock_calls[-1][1] == (4,)

    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", None, channel=4)
    ha_state = hass.states.get(entity_id)
    assert not ha_state.attributes.get(ATTR_CURRENT_TILT_POSITION)

    await async_manipulate_test_data(hass, hmip_device, "shutterLevel", None, channel=4)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN