async def test_noise_suppression_level_select(
    hass: HomeAssistant,
    satellite_config_entry: ConfigEntry,
    satellite_device: SatelliteDevice,
) -> None:
    """Test noise suppression level select."""
    nsl_entity_id = satellite_device.get_noise_suppression_level_entity_id(hass)
    assert nsl_entity_id

    state = hass.states.get(nsl_entity_id)
    assert state is not None
    assert state.state == "off"
    assert satellite_device.noise_suppression_level == 0

    # Change setting
    with patch.object(
        satellite_device, "set_noise_suppression_level"
    ) as mock_nsl_changed:
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": nsl_entity_id, "option": "max"},
            blocking=True,
        )

        state = hass.states.get(nsl_entity_id)
        assert state is not None
        assert state.state == "max"

        # set function should have been called
        mock_nsl_changed.assert_called_once_with(4)

    # test restore
    satellite_device = await reload_satellite(hass, satellite_config_entry.entry_id)

    state = hass.states.get(nsl_entity_id)
    assert state is not None
    assert state.state == "max"

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": nsl_entity_id, "option": "medium"},
        blocking=True,
    )

    assert satellite_device.noise_suppression_level == 2