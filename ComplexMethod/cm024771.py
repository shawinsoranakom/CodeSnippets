async def test_state_fails_to_update_triggers_update(hass: HomeAssistant) -> None:
    """Ensure we call async_get_properties if the turn on/off fails to update the state."""
    mocked_bulb = _mocked_bulb()
    properties = {**PROPERTIES}
    properties.pop("active_mode")
    properties["color_mode"] = "3"  # HSV
    mocked_bulb.last_properties = properties
    mocked_bulb.bulb_type = BulbType.Color
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={**CONFIG_ENTRY_DATA, CONF_NIGHTLIGHT_SWITCH: False}
    )
    config_entry.add_to_hass(hass)
    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        # We use asyncio.create_task now to avoid
        # blocking starting so we need to block again
        await hass.async_block_till_done()

    assert len(mocked_bulb.async_get_properties.mock_calls) == 1

    mocked_bulb.last_properties["power"] = "off"
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
        },
        blocking=True,
    )
    assert len(mocked_bulb.async_turn_on.mock_calls) == 1
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=1))
    await hass.async_block_till_done()
    assert len(mocked_bulb.async_get_properties.mock_calls) == 2

    mocked_bulb.last_properties["power"] = "on"
    for _ in range(5):
        await hass.services.async_call(
            "light",
            SERVICE_TURN_OFF,
            {
                ATTR_ENTITY_ID: ENTITY_LIGHT,
            },
            blocking=True,
        )
    assert len(mocked_bulb.async_turn_off.mock_calls) == 5
    # Even with five calls we only do one state request
    # since each successive call should cancel the unexpected
    # state check
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=2))
    await hass.async_block_till_done()
    assert len(mocked_bulb.async_get_properties.mock_calls) == 3

    # But if the state is correct no calls
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
        },
        blocking=True,
    )
    assert len(mocked_bulb.async_turn_on.mock_calls) == 1
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=3))
    await hass.async_block_till_done()
    assert len(mocked_bulb.async_get_properties.mock_calls) == 3