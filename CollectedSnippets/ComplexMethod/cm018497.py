async def test_rpc_energy_meter_1_sensors(
    hass: HomeAssistant, entity_registry: EntityRegistry, mock_rpc_device: Mock
) -> None:
    """Test RPC sensors for EM1 component."""
    await init_integration(hass, 2)

    assert (state := hass.states.get("sensor.test_name_energy_meter_0_power"))
    assert state.state == "85.3"

    assert (entry := entity_registry.async_get("sensor.test_name_energy_meter_0_power"))
    assert entry.unique_id == "123456789ABC-em1:0-power_em1"

    assert (state := hass.states.get("sensor.test_name_energy_meter_1_power"))
    assert state.state == "123.3"

    assert (entry := entity_registry.async_get("sensor.test_name_energy_meter_1_power"))
    assert entry.unique_id == "123456789ABC-em1:1-power_em1"

    assert (state := hass.states.get("sensor.test_name_energy_meter_0_energy"))
    assert state.state == "123.4564"

    assert (
        entry := entity_registry.async_get("sensor.test_name_energy_meter_0_energy")
    )
    assert entry.unique_id == "123456789ABC-em1data:0-total_act_energy"

    assert (state := hass.states.get("sensor.test_name_energy_meter_1_energy"))
    assert state.state == "987.6543"

    assert (
        entry := entity_registry.async_get("sensor.test_name_energy_meter_1_energy")
    )
    assert entry.unique_id == "123456789ABC-em1data:1-total_act_energy"