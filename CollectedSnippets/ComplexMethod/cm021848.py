async def test_hmip_full_flush_lock_controller_binary_sensors(
    hass: HomeAssistant,
    default_mock_hap_factory: HomeFactory,
    full_flush_lock_controller_device_data: dict[str, Any],
) -> None:
    """Test HomematicIP full flush lock controller binary sensors."""
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Universal Motorschloss Controller"],
        extra_devices=[full_flush_lock_controller_device_data],
    )

    lock_entity_id = "binary_sensor.universal_motorschloss_controller_locked"
    lock_state, hmip_device = get_and_check_entity_basics(
        hass,
        mock_hap,
        lock_entity_id,
        "Universal Motorschloss Controller Locked",
        "HmIP-FLC",
    )
    assert lock_state.state == STATE_ON

    glass_entity_id = "binary_sensor.universal_motorschloss_controller_glass_break"
    glass_state, _ = get_and_check_entity_basics(
        hass,
        mock_hap,
        glass_entity_id,
        "Universal Motorschloss Controller Glass break",
        "HmIP-FLC",
    )
    assert glass_state.state == STATE_ON

    assert hmip_device is not None
    await async_manipulate_test_data(hass, hmip_device, "lockState", "UNLOCKED")
    lock_state = hass.states.get(lock_entity_id)
    assert lock_state
    assert lock_state.state == STATE_OFF

    await async_manipulate_test_data(hass, hmip_device, "glassBroken", False)
    glass_state = hass.states.get(glass_entity_id)
    assert glass_state
    assert glass_state.state == STATE_OFF