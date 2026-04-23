async def test_sensor_network_sensors(
    freezer: FrozenDateTimeFactory,
    hass: HomeAssistant,
    mock_added_config_entry: ConfigEntry,
    mock_psutil: Mock,
) -> None:
    """Test process not exist failure."""
    network_out_sensor = hass.states.get("sensor.system_monitor_network_out_eth1")
    packets_out_sensor = hass.states.get("sensor.system_monitor_packets_out_eth1")
    throughput_network_out_sensor = hass.states.get(
        "sensor.system_monitor_network_throughput_out_eth1"
    )

    assert network_out_sensor is not None
    assert packets_out_sensor is not None
    assert throughput_network_out_sensor is not None
    assert network_out_sensor.state == "200.0"
    assert packets_out_sensor.state == "150"
    assert throughput_network_out_sensor.state == STATE_UNKNOWN

    mock_psutil.net_io_counters.return_value = {
        "eth0": snetio(200 * 1024**2, 200 * 1024**2, 100, 100, 0, 0, 0, 0),
        "eth1": snetio(400 * 1024**2, 400 * 1024**2, 300, 300, 0, 0, 0, 0),
    }

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    network_out_sensor = hass.states.get("sensor.system_monitor_network_out_eth1")
    packets_out_sensor = hass.states.get("sensor.system_monitor_packets_out_eth1")
    throughput_network_out_sensor = hass.states.get(
        "sensor.system_monitor_network_throughput_out_eth1"
    )

    assert network_out_sensor is not None
    assert packets_out_sensor is not None
    assert throughput_network_out_sensor is not None
    assert network_out_sensor.state == "400.0"
    assert packets_out_sensor.state == "300"
    assert float(throughput_network_out_sensor.state) == pytest.approx(3.493, rel=0.1)

    mock_psutil.net_io_counters.return_value = {
        "eth0": snetio(100 * 1024**2, 100 * 1024**2, 50, 50, 0, 0, 0, 0),
    }
    mock_psutil.net_if_addrs.return_value = {
        "eth0": [
            snicaddr(
                socket.AF_INET,
                "192.168.1.1",
                "255.255.255.0",
                "255.255.255.255",
                None,
            )
        ],
    }

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    network_out_sensor = hass.states.get("sensor.system_monitor_network_out_eth1")
    packets_out_sensor = hass.states.get("sensor.system_monitor_packets_out_eth1")
    throughput_network_out_sensor = hass.states.get(
        "sensor.system_monitor_network_throughput_out_eth1"
    )

    assert network_out_sensor is not None
    assert packets_out_sensor is not None
    assert throughput_network_out_sensor is not None
    assert network_out_sensor.state == STATE_UNKNOWN
    assert packets_out_sensor.state == STATE_UNKNOWN
    assert throughput_network_out_sensor.state == STATE_UNKNOWN