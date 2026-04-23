async def test_phase_count_filters_transient_zero_on_service_call(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_nrgkick_api: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that a service call keeps the cached value when refreshing returns 0.

    When the user sets a new phase count, the immediate refresh triggered
    by the service call may still see 0. The entity should keep the
    requested value instead.
    """
    await setup_integration(hass, mock_config_entry, platforms=[Platform.NUMBER])

    entity_id = "number.nrgkick_test_phase_count"

    assert (state := hass.states.get(entity_id))
    assert state.state == "3"

    # The refresh triggered by the service call will see 0.
    control_data = mock_nrgkick_api.get_control.return_value.copy()
    control_data[CONTROL_KEY_PHASE_COUNT] = 0
    mock_nrgkick_api.get_control.return_value = control_data

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 1},
        blocking=True,
    )
    mock_nrgkick_api.set_phase_count.assert_awaited_once_with(1)

    # State must not show 0; the entity keeps the cached value.
    assert (state := hass.states.get(entity_id))
    assert state.state == "1"

    # Once the device settles it reports the real phase count again.
    control_data = mock_nrgkick_api.get_control.return_value.copy()
    control_data[CONTROL_KEY_PHASE_COUNT] = 1
    mock_nrgkick_api.get_control.return_value = control_data
    prior_call_count = mock_nrgkick_api.get_control.call_count
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Verify that a periodic refresh actually occurred.
    assert mock_nrgkick_api.get_control.call_count > prior_call_count

    assert (state := hass.states.get(entity_id))
    assert state.state == "1"