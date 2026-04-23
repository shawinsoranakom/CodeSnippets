async def test_vad_sensitivity_select(
    hass: HomeAssistant,
    satellite_config_entry: ConfigEntry,
    satellite_device: SatelliteDevice,
) -> None:
    """Test VAD sensitivity select."""
    vs_entity_id = satellite_device.get_vad_sensitivity_entity_id(hass)
    assert vs_entity_id

    state = hass.states.get(vs_entity_id)
    assert state is not None
    assert state.state == VadSensitivity.DEFAULT
    assert satellite_device.vad_sensitivity == VadSensitivity.DEFAULT

    # Change setting
    with patch.object(satellite_device, "set_vad_sensitivity") as mock_vs_changed:
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": vs_entity_id, "option": VadSensitivity.AGGRESSIVE.value},
            blocking=True,
        )

        state = hass.states.get(vs_entity_id)
        assert state is not None
        assert state.state == VadSensitivity.AGGRESSIVE.value

        # set function should have been called
        mock_vs_changed.assert_called_once_with(VadSensitivity.AGGRESSIVE)

    # test restore
    satellite_device = await reload_satellite(hass, satellite_config_entry.entry_id)

    state = hass.states.get(vs_entity_id)
    assert state is not None
    assert state.state == VadSensitivity.AGGRESSIVE.value

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": vs_entity_id, "option": VadSensitivity.RELAXED.value},
        blocking=True,
    )

    assert satellite_device.vad_sensitivity == VadSensitivity.RELAXED