async def test_options_add_sensor_duplicate(
    hass: HomeAssistant, config_entry, setup_config_entry
) -> None:
    """Test adding a duplicate sensor via the options flow."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"next_step_id": "add_sensor"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "add_sensor"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "latitude": TEST_LATITUDE,
            "longitude": TEST_LONGITUDE,
            "distance": 5,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "choose_sensor"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "sensor_index": str(TEST_SENSOR_INDEX1),
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    # Unload to make sure the update does not run after the
    # mock is removed.
    await hass.config_entries.async_unload(config_entry.entry_id)