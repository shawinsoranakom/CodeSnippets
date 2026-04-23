async def test_hmip_heating_group_services(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipHeatingGroup services."""
    entity_id = "climate.badezimmer"
    entity_name = "Badezimmer"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_groups=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )
    assert ha_state

    await hass.services.async_call(
        "homematicip_cloud",
        "set_active_climate_profile",
        {"climate_profile_index": 2, "entity_id": "climate.badezimmer"},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_active_profile_async"
    assert hmip_device.mock_calls[-1][1] == (1,)
    assert len(hmip_device._connection.mock_calls) == 1

    await hass.services.async_call(
        "homematicip_cloud",
        "set_active_climate_profile",
        {"climate_profile_index": 2, "entity_id": "all"},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_active_profile_async"
    assert hmip_device.mock_calls[-1][1] == (1,)
    assert len(hmip_device._connection.mock_calls) == 2