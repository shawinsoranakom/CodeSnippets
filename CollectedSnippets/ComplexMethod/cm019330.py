async def test_sensor_inverter_detailed_data(
    hass: HomeAssistant,
    mock_envoy: AsyncMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test enphase_envoy inverter detailed entities values."""
    with patch("homeassistant.components.enphase_envoy.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)

    entity_base = f"{Platform.SENSOR}.inverter"

    for sn, inverter in mock_envoy.data.inverters.items():
        assert (dc_voltage := hass.states.get(f"{entity_base}_{sn}_dc_voltage"))
        assert float(dc_voltage.state) == (inverter.dc_voltage)
        assert (dc_current := hass.states.get(f"{entity_base}_{sn}_dc_current"))
        assert float(dc_current.state) == (inverter.dc_current)
        assert (ac_voltage := hass.states.get(f"{entity_base}_{sn}_ac_voltage"))
        assert float(ac_voltage.state) == (inverter.ac_voltage)
        assert (ac_current := hass.states.get(f"{entity_base}_{sn}_ac_current"))
        assert float(ac_current.state) == (inverter.ac_current)
        assert (frequency := hass.states.get(f"{entity_base}_{sn}_frequency"))
        assert float(frequency.state) == (inverter.ac_frequency)
        assert (temperature := hass.states.get(f"{entity_base}_{sn}_temperature"))
        assert int(temperature.state) == (inverter.temperature)
        assert (
            lifetime_energy := hass.states.get(
                f"{entity_base}_{sn}_lifetime_energy_production"
            )
        )
        assert float(lifetime_energy.state) == (inverter.lifetime_energy / 1000.0)
        assert (
            energy_produced_today := hass.states.get(
                f"{entity_base}_{sn}_energy_production_today"
            )
        )
        assert int(energy_produced_today.state) == (inverter.energy_today)
        assert (
            last_report_duration := hass.states.get(
                f"{entity_base}_{sn}_last_report_duration"
            )
        )
        assert int(last_report_duration.state) == (inverter.last_report_duration)
        assert (
            energy_produced := hass.states.get(
                f"{entity_base}_{sn}_energy_production_since_previous_report"
            )
        )
        assert float(energy_produced.state) == (inverter.energy_produced)
        assert (
            lifetime_maximum_power := hass.states.get(
                f"{entity_base}_{sn}_lifetime_maximum_power"
            )
        )
        assert int(lifetime_maximum_power.state) == (inverter.max_report_watts)