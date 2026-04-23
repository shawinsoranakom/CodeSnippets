async def test_adding_processor_to_options(
    hass: HomeAssistant, mock_added_config_entry: ConfigEntry
) -> None:
    """Test options listener."""
    process_sensor = hass.states.get("binary_sensor.system_monitor_process_systemd")
    assert process_sensor is None

    result = await hass.config_entries.options.async_init(
        mock_added_config_entry.entry_id
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_PROCESS: ["python3", "pip", "systemd"],
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "binary_sensor": {
            CONF_PROCESS: ["python3", "pip", "systemd"],
        },
        "resources": [
            "disk_use_percent_/",
            "disk_use_percent_/home/notexist/",
            "memory_free_",
            "network_out_eth0",
            "process_python3",
        ],
    }

    process_sensor = hass.states.get("binary_sensor.system_monitor_process_systemd")
    assert process_sensor is not None
    assert process_sensor.state == STATE_OFF