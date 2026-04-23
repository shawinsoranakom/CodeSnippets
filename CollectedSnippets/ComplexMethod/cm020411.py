async def test_options_add_and_configure_device(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test we can add a device."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": None,
            "port": None,
            "device": "/dev/tty123",
            "automatic_add": False,
            "devices": {},
        },
        unique_id=DOMAIN,
    )
    result = await start_options_flow(hass, entry)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "prompt_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "automatic_add": True,
            "event_code": "0913000022670e013970",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "set_device_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "data_bits": 4,
            "command_on": "xyz",
            "command_off": "xyz",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "set_device_options"
    assert result["errors"]
    assert result["errors"]["command_on"] == "invalid_input_2262_on"
    assert result["errors"]["command_off"] == "invalid_input_2262_off"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "data_bits": 4,
            "command_on": "0xE",
            "command_off": "0x7",
            "off_delay": 9,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()

    assert entry.data["automatic_add"]

    assert entry.data["devices"]["0913000022670e013970"]
    assert entry.data["devices"]["0913000022670e013970"]["off_delay"] == 9

    state = hass.states.get("binary_sensor.pt2262_226700")
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes.get("friendly_name") == "PT2262 226700"

    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    assert device_entries[0].id

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "prompt_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "automatic_add": False,
            "device": device_entries[0].id,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "set_device_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "data_bits": 4,
            "command_on": "0xE",
            "command_off": "0x7",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()

    assert entry.data["devices"]["0913000022670e013970"]
    assert "delay_off" not in entry.data["devices"]["0913000022670e013970"]