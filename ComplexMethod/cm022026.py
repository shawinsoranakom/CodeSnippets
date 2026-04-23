async def test_save_preferences(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
    mock_energy_platform,
) -> None:
    """Test we can save preferences."""
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)

    # Test saving default prefs is also valid.
    default_prefs = data.EnergyManager.default_preferences()

    await client.send_json({"id": 5, "type": "energy/save_prefs", **default_prefs})

    msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["success"]
    assert msg["result"] == default_prefs

    new_prefs = {
        "energy_sources": [
            # Grid 1: heat_pump_meter paired with return_to_grid_peak + power
            {
                "type": "grid",
                "stat_energy_from": "sensor.heat_pump_meter",
                "stat_energy_to": "sensor.return_to_grid_peak",
                "stat_cost": "heat_pump_kwh_cost",
                "stat_compensation": None,
                "entity_energy_price": None,
                "number_energy_price": None,
                "entity_energy_price_export": None,
                "number_energy_price_export": None,
                "stat_rate": "sensor.grid_power",
                "cost_adjustment_day": 1.2,
            },
            # Grid 2: heat_pump_meter_2 paired with return_to_grid_offpeak
            {
                "type": "grid",
                "stat_energy_from": "sensor.heat_pump_meter_2",
                "stat_energy_to": "sensor.return_to_grid_offpeak",
                "stat_cost": None,
                "stat_compensation": None,
                "entity_energy_price": None,
                "number_energy_price": 0.20,
                "entity_energy_price_export": None,
                "number_energy_price_export": 0.20,
                "cost_adjustment_day": 1.2,
            },
            {
                "type": "solar",
                "stat_energy_from": "my_solar_production",
                "stat_rate": "my_solar_power",
                "config_entry_solar_forecast": ["predicted_config_entry"],
            },
            {
                "type": "battery",
                "stat_energy_from": "my_battery_draining",
                "stat_energy_to": "my_battery_charging",
                "stat_rate": "my_battery_power",
            },
        ],
        "device_consumption": [
            {
                "stat_consumption": "some_device_usage",
                "name": "My Device",
                "included_in_stat": "sensor.some_other_device",
                "stat_rate": "sensor.some_device_power",
            }
        ],
        "device_consumption_water": [
            {
                "stat_consumption": "sensor.water_meter",
                "name": "Water Meter",
            }
        ],
    }

    await client.send_json({"id": 6, "type": "energy/save_prefs", **new_prefs})

    msg = await client.receive_json()

    assert msg["id"] == 6
    assert msg["success"]
    assert msg["result"] == new_prefs

    assert data.STORAGE_KEY not in hass_storage, "expected not to be written yet"

    await flush_store((await data.async_get_manager(hass))._store)

    assert hass_storage[data.STORAGE_KEY]["data"] == new_prefs

    assert await is_configured(hass)

    # Verify info reflects data.
    await client.send_json({"id": 7, "type": "energy/info"})

    msg = await client.receive_json()

    assert msg["id"] == 7
    assert msg["success"]
    assert msg["result"] == {
        "cost_sensors": {
            "sensor.heat_pump_meter_2": "sensor.heat_pump_meter_2_cost",
            "sensor.return_to_grid_offpeak": (
                "sensor.return_to_grid_offpeak_compensation"
            ),
        },
        "solar_forecast_domains": ["some_domain"],
    }

    # Prefs with limited options (defaults will be applied by schema)
    new_prefs_2 = {
        "energy_sources": [
            {
                "type": "grid",
                "stat_energy_from": "sensor.heat_pump_meter",
                "stat_energy_to": None,
                "stat_cost": None,
                "stat_compensation": None,
                "entity_energy_price": None,
                "number_energy_price": None,
                "entity_energy_price_export": None,
                "number_energy_price_export": None,
                "cost_adjustment_day": 1.2,
            },
            {
                "type": "solar",
                "stat_energy_from": "my_solar_production",
                "config_entry_solar_forecast": None,
            },
        ],
    }

    await client.send_json({"id": 8, "type": "energy/save_prefs", **new_prefs_2})

    msg = await client.receive_json()

    assert msg["id"] == 8
    assert msg["success"]
    assert msg["result"] == {**new_prefs, **new_prefs_2}