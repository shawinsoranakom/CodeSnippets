async def test_sensor(
    hass: HomeAssistant,
    mock_psutil: Mock,
    mock_os: Mock,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the sensor."""
    mock_config_entry = MockConfigEntry(
        title="System Monitor",
        domain=DOMAIN,
        data={},
        options={
            "binary_sensor": {"process": ["python3", "pip"]},
            "resources": [
                "disk_use_percent_/",
                "disk_use_percent_/home/notexist/",
                "memory_free_",
                "network_out_eth0",
                "process_python3",
            ],
        },
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    memory_sensor = hass.states.get("sensor.system_monitor_memory_free")
    assert memory_sensor is not None
    assert memory_sensor.state == "40.0"
    assert memory_sensor.attributes == {
        "state_class": "measurement",
        "unit_of_measurement": "MiB",
        "device_class": "data_size",
        "friendly_name": "System Monitor Memory free",
    }

    for entity in er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    ):
        if entity.domain == SENSOR_DOMAIN and "pressure" not in entity.entity_id:
            state = hass.states.get(entity.entity_id)
            assert state.state == snapshot(name=f"{entity.entity_id} - state")
            assert state.attributes == snapshot(name=f"{entity.entity_id} - attributes")

    # Check PSI sensors explicitly as snapshots are not effective for them
    # Check CPU pressure
    state = hass.states.get("sensor.system_monitor_cpu_pressure_some_10s_average")
    assert state.state == "1.1"
    state = hass.states.get("sensor.system_monitor_cpu_pressure_some_60s_average")
    assert state.state == "2.2"
    state = hass.states.get("sensor.system_monitor_cpu_pressure_some_300s_average")
    assert state.state == "3.3"
    state = hass.states.get("sensor.system_monitor_cpu_pressure_some_total")
    assert state.state == "12345"

    # Check Memory pressure some
    state = hass.states.get("sensor.system_monitor_memory_pressure_some_10s_average")
    assert state.state == "4.4"
    state = hass.states.get("sensor.system_monitor_memory_pressure_some_60s_average")
    assert state.state == "5.5"
    state = hass.states.get("sensor.system_monitor_memory_pressure_some_300s_average")
    assert state.state == "6.6"
    state = hass.states.get("sensor.system_monitor_memory_pressure_some_total")
    assert state.state == "54321"

    # Check Memory pressure full
    state = hass.states.get("sensor.system_monitor_memory_pressure_full_10s_average")
    assert state.state == "0.4"
    state = hass.states.get("sensor.system_monitor_memory_pressure_full_60s_average")
    assert state.state == "0.5"
    state = hass.states.get("sensor.system_monitor_memory_pressure_full_300s_average")
    assert state.state == "0.6"
    state = hass.states.get("sensor.system_monitor_memory_pressure_full_total")
    assert state.state == "432"

    # Check IO pressure some
    state = hass.states.get("sensor.system_monitor_io_pressure_some_10s_average")
    assert state.state == "7.7"
    state = hass.states.get("sensor.system_monitor_io_pressure_some_60s_average")
    assert state.state == "8.8"
    state = hass.states.get("sensor.system_monitor_io_pressure_some_300s_average")
    assert state.state == "9.9"
    state = hass.states.get("sensor.system_monitor_io_pressure_some_total")
    assert state.state == "67890"

    # Check IO pressure full
    state = hass.states.get("sensor.system_monitor_io_pressure_full_10s_average")
    assert state.state == "0.7"
    state = hass.states.get("sensor.system_monitor_io_pressure_full_60s_average")
    assert state.state == "0.8"
    state = hass.states.get("sensor.system_monitor_io_pressure_full_300s_average")
    assert state.state == "0.9"
    state = hass.states.get("sensor.system_monitor_io_pressure_full_total")
    assert state.state == "789"