async def test_sensors(hass: HomeAssistant, entity_registry: EntityRegistry) -> None:
    """Test data coming back from inverter."""
    mock_entry = _mock_config_entry()

    with (
        patch("aurorapy.client.AuroraSerialClient.connect", return_value=None),
        patch(
            "aurorapy.client.AuroraSerialClient.measure",
            side_effect=_simulated_returns,
        ),
        patch("aurorapy.client.AuroraSerialClient.alarms", return_value=["No alarm"]),
        patch(
            "aurorapy.client.AuroraSerialClient.serial_number",
            return_value="9876543",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.version",
            return_value="9.8.7.6",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.pn",
            return_value="A.B.C",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.firmware",
            return_value="1.234",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.cumulated_energy",
            side_effect=_simulated_returns,
        ),
    ):
        mock_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        power = hass.states.get("sensor.mydevicename_power_output")
        assert power
        assert power.state == "45.7"

        temperature = hass.states.get("sensor.mydevicename_temperature")
        assert temperature
        assert temperature.state == "9.9"

        energy = hass.states.get("sensor.mydevicename_total_energy")
        assert energy
        assert energy.state == "12.35"

        # Test the 'disabled by default' sensors.
        sensors = [
            ("sensor.mydevicename_grid_voltage", "235.9"),
            ("sensor.mydevicename_grid_current", "2.8"),
            ("sensor.mydevicename_grid_frequency", "50.8"),
            ("sensor.mydevicename_dc_dc_leak_current", "1.2345"),
            ("sensor.mydevicename_inverter_leak_current", "2.3456"),
            ("sensor.mydevicename_string_1_power", "12.3"),
            ("sensor.mydevicename_string_2_power", "23.5"),
            ("sensor.mydevicename_string_1_voltage", "123.5"),
            ("sensor.mydevicename_string_1_current", "1.0"),
            ("sensor.mydevicename_string_2_voltage", "234.6"),
            ("sensor.mydevicename_string_2_current", "1.2"),
            ("sensor.mydevicename_isolation_resistance", "0.1234"),
        ]
        for entity_id, _ in sensors:
            assert not hass.states.get(entity_id)
            assert (entry := entity_registry.async_get(entity_id)), (
                f"Entity registry entry for {entity_id} is missing"
            )
            assert entry.disabled
            assert entry.disabled_by is RegistryEntryDisabler.INTEGRATION

            # re-enable it
            entity_registry.async_update_entity(entity_id=entity_id, disabled_by=None)

        # must reload the integration when enabling an entity
        await hass.config_entries.async_unload(mock_entry.entry_id)
        await hass.async_block_till_done()
        assert mock_entry.state is ConfigEntryState.NOT_LOADED
        mock_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        for entity_id, value in sensors:
            item = hass.states.get(entity_id)
            assert item
            assert item.state == value