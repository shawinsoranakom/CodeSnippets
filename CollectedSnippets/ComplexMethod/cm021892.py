async def test_hmip_cover_slats_group(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test slats with HomematicipCoverShutteGroup."""
    entity_id = "cover.rollos_shuttergroup"
    entity_name = "Rollos ShutterGroup"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(test_groups=["Rollos"])

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 1)
    ha_state = hass.states.get(entity_id)

    assert ha_state.state == CoverState.CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await hass.services.async_call(
        "cover",
        "set_cover_position",
        {"entity_id": entity_id, "position": "50"},
        blocking=True,
    )
    await hass.services.async_call(
        "cover", "open_cover_tilt", {"entity_id": entity_id}, blocking=True
    )

    assert len(hmip_device.mock_calls) == service_call_counter + 2
    assert hmip_device.mock_calls[-1][0] == "set_slats_level_async"
    assert hmip_device.mock_calls[-1][1] == (0,)
    await async_manipulate_test_data(hass, hmip_device, "shutterLevel", 0.5)
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 0)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    await hass.services.async_call(
        "cover",
        "set_cover_tilt_position",
        {"entity_id": entity_id, "tilt_position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 5
    assert hmip_device.mock_calls[-1][0] == "set_slats_level_async"
    assert hmip_device.mock_calls[-1][1] == (0.5,)
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 0.5)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await hass.services.async_call(
        "cover", "close_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 7
    assert hmip_device.mock_calls[-1][0] == "set_slats_level_async"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(hass, hmip_device, "slatsLevel", 1)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await hass.services.async_call(
        "cover", "stop_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 9
    assert hmip_device.mock_calls[-1][0] == "set_shutter_stop_async"
    assert hmip_device.mock_calls[-1][1] == ()