async def test_hmip_blind_module(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipBlindModule."""
    entity_id = "cover.sonnenschutz_balkontur"
    entity_name = "Sonnenschutz Balkontür"
    device_model = "HmIP-HDM1"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 5
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100
    service_call_counter = len(hmip_device.mock_calls)

    await hass.services.async_call(
        "cover", "open_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_secondary_shading_level_async"
    assert hmip_device.mock_calls[-1][2] == {
        "primaryShadingLevel": 0.94956,
        "secondaryShadingLevel": 0,
    }

    await async_manipulate_test_data(hass, hmip_device, "primaryShadingLevel", 0)
    await async_manipulate_test_data(hass, hmip_device, "secondaryShadingLevel", 0)
    await hass.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 4

    assert hmip_device.mock_calls[-1][0] == "set_primary_shading_level_async"
    assert hmip_device.mock_calls[-1][2] == {"primaryShadingLevel": 0}

    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    await async_manipulate_test_data(hass, hmip_device, "primaryShadingLevel", 0.5)
    await async_manipulate_test_data(hass, hmip_device, "secondaryShadingLevel", 0.5)
    await hass.services.async_call(
        "cover",
        "set_cover_tilt_position",
        {"entity_id": entity_id, "tilt_position": "50"},
        blocking=True,
    )
    await hass.services.async_call(
        "cover",
        "set_cover_position",
        {"entity_id": entity_id, "position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 8

    assert hmip_device.mock_calls[-1][0] == "set_primary_shading_level_async"
    assert hmip_device.mock_calls[-1][2] == {"primaryShadingLevel": 0.5}
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await async_manipulate_test_data(hass, hmip_device, "primaryShadingLevel", 1)
    await async_manipulate_test_data(hass, hmip_device, "secondaryShadingLevel", 1)
    await hass.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    await hass.services.async_call(
        "cover", "close_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 12

    assert hmip_device.mock_calls[-1][0] == "set_secondary_shading_level_async"
    assert hmip_device.mock_calls[-1][2] == {
        "primaryShadingLevel": 1,
        "secondaryShadingLevel": 1,
    }

    ha_state = hass.states.get(entity_id)
    assert ha_state.state == CoverState.CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await hass.services.async_call(
        "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 13
    assert hmip_device.mock_calls[-1][0] == "stop_async"
    assert hmip_device.mock_calls[-1][1] == ()

    await hass.services.async_call(
        "cover", "stop_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 14
    assert hmip_device.mock_calls[-1][0] == "stop_async"
    assert hmip_device.mock_calls[-1][1] == ()

    await async_manipulate_test_data(hass, hmip_device, "secondaryShadingLevel", None)
    ha_state = hass.states.get(entity_id)
    assert not ha_state.attributes.get(ATTR_CURRENT_TILT_POSITION)

    await async_manipulate_test_data(hass, hmip_device, "primaryShadingLevel", None)
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN