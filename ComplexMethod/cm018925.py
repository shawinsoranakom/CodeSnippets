async def test_user_options_set_multiple(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    filled_device_registry: dr.DeviceRegistry,
) -> None:
    """Test configuring multiple consecutive devices in a row."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # Verify that first config step comes back with a selection list of all the 28-family devices
    for entry in dr.async_entries_for_config_entry(
        filled_device_registry, config_entry.entry_id
    ):
        filled_device_registry.async_update_device(entry.id, name_by_user="Given Name")
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["data_schema"].schema["device_selection"].options == {
        "Given Name (28.111111111111)": False,
        "Given Name (28.222222222222)": False,
        "Given Name (28.222222222223)": False,
    }

    # Verify that selecting two devices to configure comes back as a
    #  form with the first device to configure using it's long name as entry
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            INPUT_ENTRY_DEVICE_SELECTION: [
                "Given Name (28.111111111111)",
                "Given Name (28.222222222222)",
            ]
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert (
        result["description_placeholders"]["sensor_id"]
        == "Given Name (28.222222222222)"
    )

    # Verify that next sensor is coming up for configuration after the first
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"precision": "temperature"},
    )
    assert result["type"] is FlowResultType.FORM
    assert (
        result["description_placeholders"]["sensor_id"]
        == "Given Name (28.111111111111)"
    )

    # Verify that the setting for the device comes back as default when no input is given
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"precision": "temperature9"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert (
        result["data"]["device_options"]["28.222222222222"]["precision"]
        == "temperature"
    )
    assert (
        result["data"]["device_options"]["28.111111111111"]["precision"]
        == "temperature9"
    )