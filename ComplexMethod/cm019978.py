async def test_elapsed_time_sensor_restored(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_miele_client: MagicMock,
    setup_platform: None,
    device_fixture: MieleDevices,
    freezer: FrozenDateTimeFactory,
    restore_state,
    restore_state_abs,
) -> None:
    """Test that elapsed time returns the restored value when program ended."""

    entity_id = "sensor.washing_machine_elapsed_time"
    entity_id_abs = "sensor.washing_machine_finish"

    # Simulate program started
    device_fixture["DummyWasher"]["state"]["status"]["value_raw"] = 5
    device_fixture["DummyWasher"]["state"]["status"]["value_localized"] = "In use"
    device_fixture["DummyWasher"]["state"]["ProgramID"]["value_raw"] = 3
    device_fixture["DummyWasher"]["state"]["ProgramID"]["value_localized"] = (
        "Minimum iron"
    )
    device_fixture["DummyWasher"]["state"]["programPhase"]["value_raw"] = 260
    device_fixture["DummyWasher"]["state"]["programPhase"]["value_localized"] = (
        "Main wash"
    )
    device_fixture["DummyWasher"]["state"]["remainingTime"][0] = 1
    device_fixture["DummyWasher"]["state"]["remainingTime"][1] = 45
    device_fixture["DummyWasher"]["state"]["targetTemperature"][0]["value_raw"] = 3000
    device_fixture["DummyWasher"]["state"]["targetTemperature"][0][
        "value_localized"
    ] = 30.0
    device_fixture["DummyWasher"]["state"]["elapsedTime"][0] = 0
    device_fixture["DummyWasher"]["state"]["elapsedTime"][1] = 12
    device_fixture["DummyWasher"]["state"]["spinningSpeed"]["value_raw"] = 1200
    device_fixture["DummyWasher"]["state"]["spinningSpeed"]["value_localized"] = "1200"

    freezer.move_to(datetime(2025, 5, 31, 12, 30, tzinfo=UTC))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "12"
    assert hass.states.get(entity_id_abs).state == "2025-05-31T14:15:00+00:00"

    # Simulate program ended
    device_fixture["DummyWasher"]["state"]["status"]["value_raw"] = 7
    device_fixture["DummyWasher"]["state"]["status"]["value_localized"] = "Finished"
    device_fixture["DummyWasher"]["state"]["programPhase"]["value_raw"] = 267
    device_fixture["DummyWasher"]["state"]["programPhase"]["value_localized"] = (
        "Anti-crease"
    )
    device_fixture["DummyWasher"]["state"]["remainingTime"][0] = 0
    device_fixture["DummyWasher"]["state"]["remainingTime"][1] = 0
    device_fixture["DummyWasher"]["state"]["elapsedTime"][0] = 0
    device_fixture["DummyWasher"]["state"]["elapsedTime"][1] = 0

    freezer.move_to(datetime(2025, 5, 31, 14, 20, tzinfo=UTC))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # unload config entry and reload to make sure that the state is restored

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == "unavailable"
    assert hass.states.get(entity_id_abs).state == "unavailable"

    # simulate restore with state different from native value
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(
                    entity_id,
                    restore_state,
                    {
                        "unit_of_measurement": "min",
                    },
                ),
                {
                    "native_value": "12",
                    "native_unit_of_measurement": "min",
                },
            ),
            (
                State(
                    entity_id_abs,
                    restore_state_abs,
                    {"device_class": "timestamp"},
                ),
                {
                    "native_value": datetime(2025, 5, 31, 14, 15, tzinfo=UTC),
                    "native_unit_of_measurement": None,
                },
            ),
        ],
    )
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # check that elapsed time is the one restored and not the value reported by API (0)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "12"

    # check that absolute time is the one restored and not the value reported by API
    state = hass.states.get(entity_id_abs)
    assert state is not None
    assert state.state == "2025-05-31T14:15:00+00:00"