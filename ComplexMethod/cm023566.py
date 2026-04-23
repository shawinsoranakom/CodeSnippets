async def test_setup_entry_absent_measurement(hass: HomeAssistant) -> None:
    """Test for successfully loading sensor states when response does not contain all measurements."""
    with (
        patch(
            "energyflip.EnergyFlip.authenticate", return_value=None
        ) as mock_authenticate,
        patch(
            "energyflip.EnergyFlip.is_authenticated", return_value=True
        ) as mock_is_authenticated,
        patch(
            "energyflip.EnergyFlip.current_measurements",
            return_value=MOCK_LIMITED_CURRENT_MEASUREMENTS,
        ) as mock_current_measurements,
    ):
        config_entry = MockConfigEntry(
            version=1,
            domain=DOMAIN,
            title="userId",
            data={
                CONF_ID: "userId",
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
            source="test",
        )
        config_entry.add_to_hass(hass)

        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        # Assert data is loaded
        assert hass.states.get("sensor.current_power").state == "1011.66666666667"
        assert hass.states.get("sensor.current_power_in_peak").state == "unknown"
        assert hass.states.get("sensor.current_power_in_off_peak").state == "unknown"
        assert hass.states.get("sensor.current_power_out_peak").state == "unknown"
        assert hass.states.get("sensor.current_power_out_off_peak").state == "unknown"
        assert hass.states.get("sensor.current_gas").state == "unknown"
        assert hass.states.get("sensor.energy_today").state == "3.296665869"
        assert (
            hass.states.get("sensor.energy_consumption_peak_today").state == "unknown"
        )
        assert (
            hass.states.get("sensor.energy_consumption_off_peak_today").state
            == "unknown"
        )
        assert hass.states.get("sensor.energy_production_peak_today").state == "unknown"
        assert (
            hass.states.get("sensor.energy_production_off_peak_today").state
            == "unknown"
        )
        assert hass.states.get("sensor.gas_today").state == "unknown"

        # Assert mocks are called
        assert len(mock_authenticate.mock_calls) == 1
        assert len(mock_is_authenticated.mock_calls) == 1
        assert len(mock_current_measurements.mock_calls) == 1