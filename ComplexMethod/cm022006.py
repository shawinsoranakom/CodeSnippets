async def test_state_updates_zone(
    hass: HomeAssistant, hass_client_no_auth: ClientSessionGenerator, mock_panel
) -> None:
    """Test callback view."""
    await async_process_ha_core_config(
        hass,
        {"internal_url": "http://example.local:8123"},
    )

    device_config = config_flow.CONFIG_ENTRY_SCHEMA(
        {
            "host": "1.2.3.4",
            "port": 1234,
            "id": "112233445566",
            "model": "Konnected Pro",
            "access_token": "abcdefgh",
            "default_options": config_flow.OPTIONS_SCHEMA({config_flow.CONF_IO: {}}),
        }
    )

    device_options = config_flow.OPTIONS_SCHEMA(
        {
            "io": {
                "1": "Binary Sensor",
                "2": "Binary Sensor",
                "3": "Binary Sensor",
                "4": "Digital Sensor",
                "5": "Digital Sensor",
                "6": "Switchable Output",
                "out": "Switchable Output",
            },
            "binary_sensors": [
                {"zone": "1", "type": "door"},
                {"zone": "2", "type": "window", "name": "winder", "inverse": True},
                {"zone": "3", "type": "door"},
            ],
            "sensors": [
                {"zone": "4", "type": "dht"},
                {"zone": "5", "type": "ds18b20", "name": "temper"},
            ],
            "switches": [
                {
                    "zone": "out",
                    "name": "switcher",
                    "activation": "low",
                    "momentary": 50,
                    "pause": 100,
                    "repeat": 4,
                },
                {"zone": "6"},
            ],
        }
    )

    entry = MockConfigEntry(
        domain="konnected",
        title="Konnected Alarm Panel",
        data=device_config,
        options=device_options,
    )
    entry.add_to_hass(hass)

    # Add empty data field to ensure we process it correctly (possible if entry is ignored)
    entry = MockConfigEntry(domain="konnected", title="Konnected Alarm Panel", data={})
    entry.add_to_hass(hass)

    assert (
        await async_setup_component(
            hass,
            konnected.DOMAIN,
            {konnected.DOMAIN: {konnected.CONF_ACCESS_TOKEN: "1122334455"}},
        )
        is True
    )

    client = await hass_client_no_auth()

    # Test updating a binary sensor
    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "1", "state": 0},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}
    await hass.async_block_till_done()
    assert (
        hass.states.get(
            "binary_sensor.konnected_alarm_panel_konnected_445566_zone_1"
        ).state
        == "off"
    )

    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "1", "state": 1},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}
    await hass.async_block_till_done()
    assert (
        hass.states.get(
            "binary_sensor.konnected_alarm_panel_konnected_445566_zone_1"
        ).state
        == "on"
    )

    # Test updating sht sensor
    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "4", "temp": 22, "humi": 20},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}
    await hass.async_block_till_done()
    assert (
        hass.states.get(
            "sensor.konnected_alarm_panel_konnected_445566_sensor_4_humidity"
        ).state
        == "20"
    )
    assert (
        hass.states.get(
            "sensor.konnected_alarm_panel_konnected_445566_sensor_4_temperature"
        ).state
        == "22.0"
    )

    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "4", "temp": 25, "humi": 23},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}
    await hass.async_block_till_done()
    assert (
        hass.states.get(
            "sensor.konnected_alarm_panel_konnected_445566_sensor_4_humidity"
        ).state
        == "23"
    )
    assert (
        hass.states.get(
            "sensor.konnected_alarm_panel_konnected_445566_sensor_4_temperature"
        ).state
        == "25.0"
    )

    # Test updating ds sensor
    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "5", "temp": 32.0, "addr": 1},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}
    await hass.async_block_till_done()
    assert (
        hass.states.get("sensor.konnected_alarm_panel_temper_temperature").state
        == "32.0"
    )

    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "5", "temp": 42, "addr": 1},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}
    await hass.async_block_till_done()
    assert (
        hass.states.get("sensor.konnected_alarm_panel_temper_temperature").state
        == "42.0"
    )