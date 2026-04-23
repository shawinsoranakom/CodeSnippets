async def test_binary_sensor_not_created_when_value_is_none(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_saunum_client,
) -> None:
    """Test binary sensors are not created when initial value is None."""
    base_data = mock_saunum_client.async_get_data.return_value
    mock_saunum_client.async_get_data.return_value = replace(
        base_data,
        door_open=None,
        alarm_door_open=None,
        alarm_door_sensor=None,
        alarm_thermal_cutoff=None,
        alarm_internal_temp=None,
        alarm_temp_sensor_short=None,
        alarm_temp_sensor_open=None,
    )

    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.saunum_leil_door") is None
    assert hass.states.get("binary_sensor.saunum_leil_alarm_door_open") is None
    assert hass.states.get("binary_sensor.saunum_leil_alarm_door_sensor") is None
    assert hass.states.get("binary_sensor.saunum_leil_alarm_thermal_cutoff") is None
    assert hass.states.get("binary_sensor.saunum_leil_alarm_internal_temp") is None
    assert hass.states.get("binary_sensor.saunum_leil_alarm_temp_sensor_short") is None
    assert hass.states.get("binary_sensor.saunum_leil_alarm_temp_sensor_open") is None