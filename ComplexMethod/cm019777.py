async def test_migrate_unique_id(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_pythonkuma: AsyncMock,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Snapshot test states of sensor platform."""
    mock_pythonkuma.metrics.return_value = {
        "Monitor": UptimeKumaMonitor(
            monitor_name="Monitor",
            monitor_hostname="null",
            monitor_port="null",
            monitor_status=MonitorStatus.UP,
            monitor_url="test",
            monitor_tags=["tag1", "tag2:value"],
        )
    }
    mock_pythonkuma.version = UptimeKumaVersion(
        version="1.23.16", major="1", minor="23", patch="16"
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert (entity := entity_registry.async_get("sensor.monitor_status"))
    assert entity.unique_id == "123456789_Monitor_status"

    mock_pythonkuma.metrics.return_value = {
        1: UptimeKumaMonitor(
            monitor_id=1,
            monitor_name="Monitor",
            monitor_hostname="null",
            monitor_port="null",
            monitor_status=MonitorStatus.UP,
            monitor_url="test",
            monitor_tags=["tag1", "tag2:value"],
        )
    }
    mock_pythonkuma.version = UptimeKumaVersion(
        version="2.0.2", major="2", minor="0", patch="2"
    )
    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (entity := entity_registry.async_get("sensor.monitor_status"))
    assert entity.unique_id == "123456789_1_status"

    assert (
        device := device_registry.async_get_device(
            identifiers={(DOMAIN, f"{entity.config_entry_id}_1")}
        )
    )
    assert device.sw_version == "2.0.2"