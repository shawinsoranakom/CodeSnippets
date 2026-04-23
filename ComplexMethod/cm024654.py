async def test_add_and_remove_processes(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test adding and removing process sensors."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=config_entries.SOURCE_USER,
        data={},
        options={},
        entry_id="1",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_PROCESS: ["systemd"],
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "binary_sensor": {
            CONF_PROCESS: ["systemd"],
        }
    }

    # Add another
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_PROCESS: ["systemd", "octave-cli"],
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "binary_sensor": {
            CONF_PROCESS: ["systemd", "octave-cli"],
        },
    }

    assert (
        entity_registry.async_get("binary_sensor.system_monitor_process_systemd")
        is not None
    )
    assert (
        entity_registry.async_get("binary_sensor.system_monitor_process_octave_cli")
        is not None
    )

    # Remove one
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_PROCESS: ["systemd"],
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "binary_sensor": {
            CONF_PROCESS: ["systemd"],
        },
    }

    # Remove last
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_PROCESS: [],
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "binary_sensor": {CONF_PROCESS: []},
    }

    assert (
        entity_registry.async_get("binary_sensor.systemmonitor_process_systemd") is None
    )
    assert (
        entity_registry.async_get("binary_sensor.systemmonitor_process_octave_cli")
        is None
    )