async def test_options_replace_control_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we can replace a control device."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": None,
            "port": None,
            "device": "/dev/tty123",
            "automatic_add": False,
            "devices": {
                "0b1100100118cdea02010f70": {
                    "device_id": ["11", "0", "118cdea:2"],
                },
                "0b1100101118cdea02010f70": {
                    "device_id": ["11", "0", "1118cdea:2"],
                },
            },
        },
        unique_id=DOMAIN,
    )
    await start_options_flow(hass, entry)

    state = hass.states.get("binary_sensor.ac_118cdea_2")
    assert state
    state = hass.states.get("sensor.ac_118cdea_2_signal_strength")
    assert state
    state = hass.states.get("switch.ac_118cdea_2")
    assert state
    state = hass.states.get("binary_sensor.ac_1118cdea_2")
    assert state
    state = hass.states.get("sensor.ac_1118cdea_2_signal_strength")
    assert state
    state = hass.states.get("switch.ac_1118cdea_2")
    assert state

    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    old_device = next(
        (
            elem.id
            for elem in device_entries
            if next(iter(elem.identifiers))[1:] == ("11", "0", "118cdea:2")
        ),
        None,
    )
    new_device = next(
        (
            elem.id
            for elem in device_entries
            if next(iter(elem.identifiers))[1:] == ("11", "0", "1118cdea:2")
        ),
        None,
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "prompt_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "automatic_add": False,
            "device": old_device,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "set_device_options"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "replace_device": new_device,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    await hass.async_block_till_done()

    entry = entity_registry.async_get("binary_sensor.ac_118cdea_2")
    assert entry
    assert entry.device_id == new_device
    entry = entity_registry.async_get("sensor.ac_118cdea_2_signal_strength")
    assert entry
    assert entry.device_id == new_device
    entry = entity_registry.async_get("switch.ac_118cdea_2")
    assert entry
    assert entry.device_id == new_device

    state = hass.states.get("binary_sensor.ac_1118cdea_2")
    assert not state
    state = hass.states.get("sensor.ac_1118cdea_2_signal_strength")
    assert not state
    state = hass.states.get("switch.ac_1118cdea_2")
    assert not state