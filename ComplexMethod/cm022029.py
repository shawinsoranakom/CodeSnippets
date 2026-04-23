async def test_cost_sensor_price_entity_total_no_reset(
    frozen_time,
    setup_integration,
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    hass_ws_client: WebSocketGenerator,
    entity_registry: er.EntityRegistry,
    initial_energy,
    initial_cost,
    price_entity,
    fixed_price,
    usage_sensor_entity_id,
    cost_sensor_entity_id,
    flow_type,
    energy_source_data: dict[str, Any],
    price_update_key: str,
    energy_state_class,
) -> None:
    """Test energy cost price from total type sensor entity with no last_reset."""

    def _compile_statistics(_):
        with session_scope(hass=hass) as session:
            return compile_statistics(
                hass, session, now, now + timedelta(seconds=1), {}
            ).platform_stats

    energy_attributes = {
        ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
        ATTR_STATE_CLASS: energy_state_class,
    }

    energy_data = data.EnergyManager.default_preferences()
    # Build energy source from test parameter data, adding price fields
    energy_source = copy.deepcopy(energy_source_data)
    if flow_type == "flow_from":
        energy_source["entity_energy_price"] = price_entity
        energy_source["number_energy_price"] = fixed_price
    else:
        energy_source["entity_energy_price_export"] = price_entity
        energy_source["number_energy_price_export"] = fixed_price
    energy_data["energy_sources"].append(energy_source)

    hass_storage[data.STORAGE_KEY] = {
        "version": 1,
        "data": energy_data,
    }

    now = dt_util.utcnow()
    last_reset_cost_sensor = now.isoformat()

    # Optionally initialize dependent entities
    if initial_energy is not None:
        hass.states.async_set(
            usage_sensor_entity_id,
            initial_energy,
            energy_attributes,
        )
    hass.states.async_set("sensor.energy_price", "1")

    await setup_integration(hass)

    state = hass.states.get(cost_sensor_entity_id)
    assert state.state == initial_cost
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.MONETARY
    if initial_cost != "unknown":
        assert state.attributes[ATTR_LAST_RESET] == last_reset_cost_sensor
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.TOTAL
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "EUR"

    # Optional late setup of dependent entities
    if initial_energy is None:
        hass.states.async_set(
            usage_sensor_entity_id,
            "0",
            energy_attributes,
        )
        await hass.async_block_till_done()

    state = hass.states.get(cost_sensor_entity_id)
    assert state.state == "0.0"
    assert state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.MONETARY
    assert state.attributes[ATTR_LAST_RESET] == last_reset_cost_sensor
    assert state.attributes[ATTR_STATE_CLASS] == SensorStateClass.TOTAL
    assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "EUR"

    entry = entity_registry.async_get(cost_sensor_entity_id)
    assert entry
    postfix = "cost" if flow_type == "flow_from" else "compensation"
    assert entry.unique_id == f"{usage_sensor_entity_id}_grid_{postfix}"
    assert entry.hidden_by is er.RegistryEntryHider.INTEGRATION

    # Energy use bumped to 10 kWh
    frozen_time.tick(TEST_TIME_ADVANCE_INTERVAL)
    hass.states.async_set(
        usage_sensor_entity_id,
        "10",
        energy_attributes,
    )
    await hass.async_block_till_done()
    state = hass.states.get(cost_sensor_entity_id)
    assert state.state == "10.0"  # 0 EUR + (10-0) kWh * 1 EUR/kWh = 10 EUR
    assert state.attributes[ATTR_LAST_RESET] == last_reset_cost_sensor

    # Nothing happens when price changes
    if price_entity is not None:
        hass.states.async_set(price_entity, "2")
        await hass.async_block_till_done()
    else:
        energy_data = copy.deepcopy(energy_data)
        energy_data["energy_sources"][0][price_update_key] = 2
        client = await hass_ws_client(hass)
        await client.send_json({"id": 5, "type": "energy/save_prefs", **energy_data})
        msg = await client.receive_json()
        assert msg["success"]
    state = hass.states.get(cost_sensor_entity_id)
    assert state.state == "10.0"  # 10 EUR + (10-10) kWh * 2 EUR/kWh = 10 EUR
    assert state.attributes[ATTR_LAST_RESET] == last_reset_cost_sensor

    # Additional consumption is using the new price
    frozen_time.tick(TEST_TIME_ADVANCE_INTERVAL)
    hass.states.async_set(
        usage_sensor_entity_id,
        "14.5",
        energy_attributes,
    )
    await hass.async_block_till_done()
    state = hass.states.get(cost_sensor_entity_id)
    assert state.state == "19.0"  # 10 EUR + (14.5-10) kWh * 2 EUR/kWh = 19 EUR
    assert state.attributes[ATTR_LAST_RESET] == last_reset_cost_sensor

    # Check generated statistics
    await async_wait_recording_done(hass)
    all_statistics = await hass.loop.run_in_executor(None, _compile_statistics, hass)
    statistics = get_statistics_for_entity(all_statistics, cost_sensor_entity_id)
    assert statistics["stat"]["sum"] == 19.0

    # Energy sensor has a small dip
    frozen_time.tick(TEST_TIME_ADVANCE_INTERVAL)
    hass.states.async_set(
        usage_sensor_entity_id,
        "14",
        energy_attributes,
    )
    await hass.async_block_till_done()
    state = hass.states.get(cost_sensor_entity_id)
    assert state.state == "18.0"  # 19 EUR + (14-14.5) kWh * 2 EUR/kWh = 18 EUR
    assert state.attributes[ATTR_LAST_RESET] == last_reset_cost_sensor

    # Check generated statistics
    await async_wait_recording_done(hass)
    all_statistics = await hass.loop.run_in_executor(None, _compile_statistics, hass)
    statistics = get_statistics_for_entity(all_statistics, cost_sensor_entity_id)
    assert statistics["stat"]["sum"] == 18.0