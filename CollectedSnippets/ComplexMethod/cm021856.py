async def test_hmip_add_device(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    default_mock_hap_factory: HomeFactory,
    hmip_config_entry: MockConfigEntry,
) -> None:
    """Test Remove of hmip device."""
    entity_id = "light.treppe_ch"
    entity_name = "Treppe CH"
    device_model = "HmIP-BSL"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Treppe"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert hmip_device

    pre_device_count = len(device_registry.devices)
    pre_entity_count = len(entity_registry.entities)
    pre_mapping_count = len(mock_hap.hmip_device_by_entity_id)

    hmip_device.fire_remove_event()
    await hass.async_block_till_done()

    assert len(device_registry.devices) == pre_device_count - 1
    assert len(entity_registry.entities) == pre_entity_count - 3
    assert len(mock_hap.hmip_device_by_entity_id) == pre_mapping_count - 3

    reloaded_hap = HomematicipHAP(hass, hmip_config_entry)
    with (
        patch(
            "homeassistant.components.homematicip_cloud.HomematicipHAP",
            return_value=reloaded_hap,
        ),
        patch.object(reloaded_hap, "async_connect"),
        patch.object(reloaded_hap, "get_hap", return_value=mock_hap.home),
        patch(
            "homeassistant.components.homematicip_cloud.hap.asyncio.sleep",
        ),
    ):
        mock_hap.home.fire_create_event(event_type=EventType.DEVICE_ADDED)
        await hass.async_block_till_done()

    assert len(device_registry.devices) == pre_device_count
    assert len(entity_registry.entities) == pre_entity_count
    new_hap = hmip_config_entry.runtime_data
    assert len(new_hap.hmip_device_by_entity_id) == pre_mapping_count