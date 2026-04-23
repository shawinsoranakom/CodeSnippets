async def test_delta_report_sensor(
    hass: HomeAssistant,
    mock_manager: Manager,
    mock_config_entry: MockConfigEntry,
    mock_device: CustomerDevice,
    mock_listener: MockDeviceListener,
) -> None:
    """Test delta report sensor behavior."""
    await initialize_entry(hass, mock_manager, mock_config_entry, mock_device)
    entity_id = "sensor.ha_socket_delta_test_total_energy"
    timestamp = 1000

    # Delta sensors start from zero and accumulate values
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "0"
    assert state.attributes["state_class"] == SensorStateClass.TOTAL_INCREASING

    # Send delta update
    await mock_listener.async_send_device_update(
        mock_device,
        {"add_ele": 200},
        {"add_ele": timestamp},
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(0.2)

    # Send delta update (multiple dpcode)
    timestamp += 100
    await mock_listener.async_send_device_update(
        mock_device,
        {"add_ele": 300, "switch_1": True},
        {"add_ele": timestamp, "switch_1": timestamp},
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(0.5)

    # Send delta update (timestamp not incremented)
    await mock_listener.async_send_device_update(
        mock_device,
        {"add_ele": 500},
        {"add_ele": timestamp},  # same timestamp
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(0.5)  # unchanged

    # Send delta update (unrelated dpcode)
    await mock_listener.async_send_device_update(
        mock_device,
        {"switch_1": False},
        {"switch_1": timestamp + 100},
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(0.5)  # unchanged

    # Send delta update
    timestamp += 100
    await mock_listener.async_send_device_update(
        mock_device,
        {"add_ele": 100},
        {"add_ele": timestamp},
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(0.6)

    # Send delta update (None value)
    timestamp += 100
    mock_device.status["add_ele"] = None
    await mock_listener.async_send_device_update(
        mock_device,
        {"add_ele": None},
        {"add_ele": timestamp},
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(0.6)  # unchanged

    # Send delta update (no timestamp - skipped)
    mock_device.status["add_ele"] = 200
    await mock_listener.async_send_device_update(
        mock_device,
        {"add_ele": 200},
        None,
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == pytest.approx(0.6)