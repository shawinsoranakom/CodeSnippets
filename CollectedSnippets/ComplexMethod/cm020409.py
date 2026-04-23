async def test_options_replace_sensor_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we can replace a sensor device."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": None,
            "port": None,
            "device": "/dev/tty123",
            "automatic_add": False,
            "devices": {
                "0a520101f00400e22d0189": {"device_id": ["52", "1", "f0:04"]},
                "0a520105230400c3260279": {"device_id": ["52", "1", "23:04"]},
            },
        },
        unique_id=DOMAIN,
    )
    await start_options_flow(hass, entry)

    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_signal_strength"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_battery"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_humidity"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_humidity_status"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_temperature"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_signal_strength"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_battery"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_humidity"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_humidity_status"
    )
    assert state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_temperature"
    )
    assert state

    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    old_device = next(
        (
            elem.id
            for elem in device_entries
            if next(iter(elem.identifiers))[1:] == ("52", "1", "f0:04")
        ),
        None,
    )
    new_device = next(
        (
            elem.id
            for elem in device_entries
            if next(iter(elem.identifiers))[1:] == ("52", "1", "23:04")
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

    entry = entity_registry.async_get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_signal_strength"
    )
    assert entry
    assert entry.device_id == new_device
    entry = entity_registry.async_get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_humidity"
    )
    assert entry
    assert entry.device_id == new_device
    entry = entity_registry.async_get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_humidity_status"
    )
    assert entry
    assert entry.device_id == new_device
    entry = entity_registry.async_get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_battery"
    )
    assert entry
    assert entry.device_id == new_device
    entry = entity_registry.async_get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_f0_04_temperature"
    )
    assert entry
    assert entry.device_id == new_device

    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_signal_strength"
    )
    assert not state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_battery"
    )
    assert not state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_humidity"
    )
    assert not state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_humidity_status"
    )
    assert not state
    state = hass.states.get(
        "sensor.thgn122_123_thgn132_thgr122_228_238_268_23_04_temperature"
    )
    assert not state