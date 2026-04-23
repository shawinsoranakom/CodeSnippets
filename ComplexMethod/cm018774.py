async def test_phase_count_filters_transient_zero_on_poll(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nrgkick_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that a transient phase count of 0 from a poll is filtered.

    During a phase-count switch the device briefly reports 0 phases.
    A coordinator refresh must not expose the transient value.
    """
    await setup_integration(hass, mock_config_entry, platforms=[Platform.NUMBER])

    entity_id = "number.nrgkick_test_phase_count"

    assert (state := hass.states.get(entity_id))
    assert state.state == "3"

    # One refresh happened during setup.
    assert mock_nrgkick_api.get_control.call_count == 1

    # Device briefly reports 0 during a phase switch.
    control_data = mock_nrgkick_api.get_control.return_value.copy()
    control_data[CONTROL_KEY_PHASE_COUNT] = 0
    mock_nrgkick_api.get_control.return_value = control_data
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify the coordinator actually polled the device.
    assert mock_nrgkick_api.get_control.call_count == 2

    # The transient 0 must not surface; state stays at the previous value.
    assert (state := hass.states.get(entity_id))
    assert state.state == "3"

    # Once the device settles it reports the real phase count.
    control_data = mock_nrgkick_api.get_control.return_value.copy()
    control_data[CONTROL_KEY_PHASE_COUNT] = 1
    mock_nrgkick_api.get_control.return_value = control_data
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify the coordinator polled again.
    assert mock_nrgkick_api.get_control.call_count == 3

    assert (state := hass.states.get(entity_id))
    assert state.state == "1"