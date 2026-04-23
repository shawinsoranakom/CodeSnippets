async def test_a01_switch_unknown_state(
    hass: HomeAssistant,
    setup_entry: MockConfigEntry,
    fake_devices: list[FakeDevice],
) -> None:
    """Test A01 switch returns unknown when API omits the protocol key."""
    entity_id = "switch.zeo_one_sound_setting"

    # Verify entity exists with a known state initially
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"

    # Simulate the API returning data without the SOUND_SET key
    washing_machine = next(
        device
        for device in fake_devices
        if hasattr(device, "zeo") and device.zeo is not None
    )
    incomplete_data = {
        k: v
        for k, v in washing_machine.zeo.query_values.return_value.items()
        if k != RoborockZeoProtocol.SOUND_SET
    }
    washing_machine.zeo.query_values.return_value = incomplete_data

    # Trigger a coordinator refresh
    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=61),
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "unknown"