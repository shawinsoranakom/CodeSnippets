async def test_options_flow_defaults(
    async_setup_entry,
    async_unload_effect,
    input_flow_control,
    conf_flow_control,
    hass: HomeAssistant,
) -> None:
    """Test options flow defaults match radio defaults."""

    entry = MockConfigEntry(
        version=config_flow.ZhaConfigFlowHandler.VERSION,
        domain=DOMAIN,
        data={
            CONF_DEVICE: {
                CONF_DEVICE_PATH: "/dev/ttyUSB0",
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

    async_setup_entry.reset_mock()

    # ZHA gets unloaded
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload",
        new_callable=DelayedAsyncMock,
        side_effect=[async_unload_effect],
    ) as mock_async_unload:
        result1 = await hass.config_entries.options.async_configure(
            flow["flow_id"], user_input={}
        )

    mock_async_unload.assert_called_once_with(entry.entry_id)

    # Unload it ourselves
    entry.mock_state(hass, ConfigEntryState.NOT_LOADED)

    # Reconfigure ZHA
    assert result1["step_id"] == "prompt_migrate_or_reconfigure"
    result2 = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={"next_step_id": config_flow.OptionsMigrationIntent.RECONFIGURE},
    )

    # Current path is the default
    assert result2["step_id"] == "choose_serial_port"
    assert "/dev/ttyUSB0" in result2["data_schema"]({})[CONF_DEVICE_PATH]

    # Autoprobing fails, we have to manually choose the radio type
    result3 = await hass.config_entries.options.async_configure(
        flow["flow_id"], user_input={}
    )

    # Current radio type is the default
    assert result3["step_id"] == "manual_pick_radio_type"
    assert result3["data_schema"]({})[CONF_RADIO_TYPE] == RadioType.znp.description

    # Continue on to port settings
    result4 = await hass.config_entries.options.async_configure(
        flow["flow_id"],
        user_input={
            CONF_RADIO_TYPE: RadioType.znp.description,
        },
    )

    # The defaults match our current settings
    assert result4["step_id"] == "manual_port_config"
    assert entry.data[CONF_DEVICE] == {
        "path": "/dev/ttyUSB0",
        "baudrate": 12345,
        "flow_control": None,
    }
    assert result4["data_schema"]({}) == {
        "path": "/dev/ttyUSB0",
        "baudrate": 12345,
        "flow_control": "none",
    }

    with patch(
        f"zigpy_znp.{PROBE_FUNCTION_PATH}", AsyncMock(return_value=True)
    ) as mock_probe:
        # Change the serial port path
        result5 = await hass.config_entries.options.async_configure(
            flow["flow_id"],
            user_input={
                # Change everything
                CONF_DEVICE_PATH: "/dev/new_serial_port",
                CONF_BAUDRATE: 54321,
                CONF_FLOW_CONTROL: input_flow_control,
            },
        )
        # verify we passed the correct flow control to the probe function
        assert mock_probe.mock_calls == [
            call(
                {
                    "path": "/dev/new_serial_port",
                    "baudrate": 54321,
                    "flow_control": conf_flow_control,
                }
            )
        ]

    # The radio has been detected, we can move on to creating the config entry
    assert result5["step_id"] == "choose_migration_strategy"

    async_setup_entry.assert_not_called()

    result6 = await hass.config_entries.options.async_configure(
        result5["flow_id"],
        user_input={"next_step_id": config_flow.MIGRATION_STRATEGY_ADVANCED},
    )
    await hass.async_block_till_done()

    result7 = await hass.config_entries.options.async_configure(
        result6["flow_id"],
        user_input={"next_step_id": config_flow.FORMATION_REUSE_SETTINGS},
    )
    await hass.async_block_till_done()

    assert result7["type"] is FlowResultType.ABORT
    assert result7["reason"] == "reconfigure_successful"

    # The updated entry contains correct settings
    assert entry.data == {
        CONF_DEVICE: {
            CONF_DEVICE_PATH: "/dev/new_serial_port",
            CONF_BAUDRATE: 54321,
            CONF_FLOW_CONTROL: conf_flow_control,
        },
        CONF_RADIO_TYPE: "znp",
    }

    # ZHA was started again
    assert async_setup_entry.call_count == 1