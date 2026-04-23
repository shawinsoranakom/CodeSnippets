async def test_manual_offline_mode(
    hass: HomeAssistant,
    mock_lamarzocco: MagicMock,
    mock_config_entry_bluetooth: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
    mock_ble_device_from_address: MagicMock,
) -> None:
    """Test that manual offline mode successfully sets up and updates entities via Bluetooth, and marks non-Bluetooth entities as unavailable."""

    mock_config_entry_bluetooth.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry_bluetooth, options={CONF_OFFLINE_MODE: True}
    )
    await hass.config_entries.async_setup(mock_config_entry_bluetooth.entry_id)
    await hass.async_block_till_done()

    main_switch = f"switch.{mock_lamarzocco.serial_number}"
    state = hass.states.get(main_switch)
    assert state
    assert state.state == STATE_ON

    # Simulate Bluetooth update changing machine mode to standby
    mock_lamarzocco.dashboard.config[
        WidgetType.CM_MACHINE_STATUS
    ].mode = MachineMode.STANDBY

    # Trigger Bluetooth coordinator update
    freezer.tick(timedelta(seconds=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify entity state was updated
    state = hass.states.get(main_switch)
    assert state
    assert state.state == STATE_OFF

    # verify other entities are unavailable
    sample_entities = (
        f"binary_sensor.{mock_lamarzocco.serial_number}_backflush_active",
        f"update.{mock_lamarzocco.serial_number}_gateway_firmware",
    )
    for entity_id in sample_entities:
        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_UNAVAILABLE