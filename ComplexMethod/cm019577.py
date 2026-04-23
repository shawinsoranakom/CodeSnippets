async def test_vacuum_operational_error_sensor(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test RVC Operational Error sensor, using a vacuum cleaner fixture."""
    # RvcOperationalState Cluster / OperationalError attribute (1/97/5)
    state = hass.states.get("sensor.mock_vacuum_operational_error")
    assert state
    assert state.state == "no_error"
    assert state.attributes["options"] == [
        "no_error",
        "unable_to_start_or_resume",
        "unable_to_complete_operation",
        "command_invalid_in_state",
        "failed_to_find_charging_dock",
        "stuck",
        "dust_bin_missing",
        "dust_bin_full",
        "water_tank_empty",
        "water_tank_missing",
        "water_tank_lid_open",
        "mop_cleaning_pad_missing",
        "low_battery",
        "cannot_reach_target_area",
        "dirty_water_tank_full",
        "dirty_water_tank_missing",
        "wheels_jammed",
        "brush_jammed",
        "navigation_sensor_obscured",
    ]
    # test Rvc error
    set_node_attribute(matter_node, 1, 97, 5, {0: 66})
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_vacuum_operational_error")
    assert state
    assert state.state == "dust_bin_missing"

    # test unknown errorStateID == 192 (0xC0)
    set_node_attribute(matter_node, 1, 97, 5, {0: 192})
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("sensor.mock_vacuum_operational_error")
    assert state
    assert state.state == "unknown"