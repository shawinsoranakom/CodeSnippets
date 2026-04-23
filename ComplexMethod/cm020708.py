async def test_options_flow_defaults_socket(hass: HomeAssistant) -> None:
    """Test options flow defaults work even for serial ports that can't be listed."""

    entry = MockConfigEntry(
        version=config_flow.ZhaConfigFlowHandler.VERSION,
        domain=DOMAIN,
        data={
            CONF_DEVICE: {
                CONF_DEVICE_PATH: "socket://localhost:5678",
                CONF_BAUDRATE: 12345,
                CONF_FLOW_CONTROL: None,
            },
            CONF_RADIO_TYPE: "znp",
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flow = await hass.config_entries.options.async_init(entry.entry_id)

    # ZHA gets unloaded
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload", return_value=True
    ):
        result1 = await hass.config_entries.options.async_configure(
            flow["flow_id"], user_input={}
        )

    assert result1["step_id"] == "prompt_migrate_or_reconfigure"
    result2 = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={"next_step_id": config_flow.OptionsMigrationIntent.RECONFIGURE},
    )

    # Radio path must be manually entered
    assert result2["step_id"] == "choose_serial_port"
    assert result2["data_schema"]({})[CONF_DEVICE_PATH] == config_flow.CONF_MANUAL_PATH

    result3 = await hass.config_entries.options.async_configure(
        flow["flow_id"], user_input={}
    )

    # Current radio type is the default
    assert result3["step_id"] == "manual_pick_radio_type"
    assert result3["data_schema"]({})[CONF_RADIO_TYPE] == RadioType.znp.description

    # Continue on to port settings
    result4 = await hass.config_entries.options.async_configure(
        flow["flow_id"], user_input={}
    )

    # The defaults match our current settings
    assert result4["step_id"] == "manual_port_config"
    assert entry.data[CONF_DEVICE] == {
        "path": "socket://localhost:5678",
        "baudrate": 12345,
        "flow_control": None,
    }
    assert result4["data_schema"]({}) == {
        "path": "socket://localhost:5678",
        "baudrate": 12345,
        "flow_control": "none",
    }

    with patch(f"zigpy_znp.{PROBE_FUNCTION_PATH}", AsyncMock(return_value=True)):
        result5 = await hass.config_entries.options.async_configure(
            flow["flow_id"], user_input={}
        )

    assert result5["step_id"] == "choose_migration_strategy"