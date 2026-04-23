async def test_schedule_enabled_switch_on_off(hass: HomeAssistant) -> None:
    """Test the schedule enabled switch."""

    entry = mock_config_entry(hass)

    with (
        patch_async_ble_device_from_address(),
        patch_melnor_device() as device_patch,
        patch_async_register_callback(),
    ):
        device = device_patch.return_value

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        switch = hass.states.get("switch.zone_1_schedule")

        assert switch is not None
        assert switch.state is STATE_OFF
        assert device.zone1.schedule_enabled is False

        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.zone_1_schedule"},
            blocking=True,
        )

        switch = hass.states.get("switch.zone_1_schedule")

        assert switch is not None
        assert switch.state is STATE_ON
        assert device.zone1.schedule_enabled is True