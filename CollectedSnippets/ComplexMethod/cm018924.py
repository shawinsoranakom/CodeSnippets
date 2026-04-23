async def test_user_options_empty_selection_recovery(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test leaving the selection of devices empty."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # Verify that first config step comes back with a selection list of all the 28-family devices
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["data_schema"].schema["device_selection"].options == {
        "28.111111111111": False,
        "28.222222222222": False,
        "28.222222222223": False,
    }

    # Verify that an empty selection shows the form again
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={INPUT_ENTRY_DEVICE_SELECTION: []},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_selection"
    assert result["errors"] == {"base": "device_not_selected"}

    # Verify that a single selected device to configure comes back as a form with the device to configure
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={INPUT_ENTRY_DEVICE_SELECTION: ["28.111111111111"]},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["description_placeholders"]["sensor_id"] == "28.111111111111"

    # Verify that the setting for the device comes back as default when no input is given
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert (
        result["data"]["device_options"]["28.111111111111"]["precision"]
        == "temperature"
    )