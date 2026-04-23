async def test_hmip_doorlockdrive(
    hass: HomeAssistant, default_mock_hap_factory: HomeFactory
) -> None:
    """Test HomematicipDoorLockDrive."""
    entity_id = "lock.haustuer"
    entity_name = "Haustuer"
    device_model = "HmIP-DLD"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
        hass, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.attributes[ATTR_SUPPORTED_FEATURES] == LockEntityFeature.OPEN

    await hass.services.async_call(
        "lock",
        "open",
        {"entity_id": entity_id},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_lock_state_async"
    assert hmip_device.mock_calls[-1][1] == (HomematicLockState.OPEN,)

    await hass.services.async_call(
        "lock",
        "lock",
        {"entity_id": entity_id},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "set_lock_state_async"
    assert hmip_device.mock_calls[-1][1] == (HomematicLockState.LOCKED,)

    await hass.services.async_call(
        "lock",
        "unlock",
        {"entity_id": entity_id},
        blocking=True,
    )

    assert hmip_device.mock_calls[-1][0] == "set_lock_state_async"
    assert hmip_device.mock_calls[-1][1] == (HomematicLockState.UNLOCKED,)

    await async_manipulate_test_data(
        hass, hmip_device, "motorState", MotorState.CLOSING
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == LockState.LOCKING

    await async_manipulate_test_data(
        hass, hmip_device, "motorState", MotorState.OPENING
    )
    ha_state = hass.states.get(entity_id)
    assert ha_state.state == LockState.UNLOCKING