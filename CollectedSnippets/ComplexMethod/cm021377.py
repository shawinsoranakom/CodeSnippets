async def test_climate(
    api_return_value: dict[str, Any],
    expected_state: HVACMode,
    expected_current_temperature: int,
    expected_temperature: int,
    expected_hvac_action: HVACAction,
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test Broadlink climate."""

    device = get_device("Guest room")
    mock_api = device.get_mock_api()
    mock_api.get_full_status.return_value = api_return_value
    mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, mock_setup.entry.unique_id)}
    )
    entries = er.async_entries_for_device(entity_registry, device_entry.id)
    climates = [entry for entry in entries if entry.domain == Platform.CLIMATE]
    assert len(climates) == 1

    climate = climates[0]

    await async_update_entity(hass, climate.entity_id)
    assert mock_setup.api.get_full_status.call_count == 2
    state = hass.states.get(climate.entity_id)
    assert state.state == expected_state
    assert state.attributes["current_temperature"] == expected_current_temperature
    assert state.attributes["temperature"] == expected_temperature
    assert state.attributes["hvac_action"] == expected_hvac_action