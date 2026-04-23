async def test_api(
    hass: HomeAssistant, hass_client_no_auth: ClientSessionGenerator, mock_panel
) -> None:
    """Test callback view."""
    await async_setup_component(hass, "http", {"http": {}})

    device_config = config_flow.CONFIG_ENTRY_SCHEMA(
        {
            "host": "1.2.3.4",
            "port": 1234,
            "id": "112233445566",
            "model": "Konnected Pro",
            "access_token": "abcdefgh",
            "api_host": "http://192.168.86.32:8123",
            "default_options": config_flow.OPTIONS_SCHEMA({config_flow.CONF_IO: {}}),
        }
    )

    device_options = config_flow.OPTIONS_SCHEMA(
        {
            "api_host": "http://192.168.86.32:8123",
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

    assert (
        await async_setup_component(
            hass,
            konnected.DOMAIN,
            {konnected.DOMAIN: {konnected.CONF_ACCESS_TOKEN: "globaltoken"}},
        )
        is True
    )

    client = await hass_client_no_auth()

    # Test the get endpoint for switch status polling
    resp = await client.get("/api/konnected")
    assert resp.status == HTTPStatus.NOT_FOUND  # no device provided

    resp = await client.get("/api/konnected/223344556677")
    assert resp.status == HTTPStatus.NOT_FOUND  # unknown device provided

    resp = await client.get("/api/konnected/device/112233445566")
    assert resp.status == HTTPStatus.NOT_FOUND  # no zone provided
    result = await resp.json()
    assert result == {"message": "Switch on zone or pin unknown not configured"}

    resp = await client.get("/api/konnected/device/112233445566?zone=8")
    assert resp.status == HTTPStatus.NOT_FOUND  # invalid zone
    result = await resp.json()
    assert result == {"message": "Switch on zone or pin 8 not configured"}

    resp = await client.get("/api/konnected/device/112233445566?pin=12")
    assert resp.status == HTTPStatus.NOT_FOUND  # invalid pin
    result = await resp.json()
    assert result == {"message": "Switch on zone or pin 12 not configured"}

    resp = await client.get("/api/konnected/device/112233445566?zone=out")
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"state": 1, "zone": "out"}

    resp = await client.get("/api/konnected/device/112233445566?pin=8")
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"state": 1, "pin": "8"}

    # Test the post endpoint for sensor updates
    resp = await client.post("/api/konnected/device", json={"zone": "1", "state": 1})
    assert resp.status == HTTPStatus.NOT_FOUND

    resp = await client.post(
        "/api/konnected/device/112233445566", json={"zone": "1", "state": 1}
    )
    assert resp.status == HTTPStatus.UNAUTHORIZED
    result = await resp.json()
    assert result == {"message": "unauthorized"}

    resp = await client.post(
        "/api/konnected/device/223344556677",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "1", "state": 1},
    )
    assert resp.status == HTTPStatus.BAD_REQUEST

    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "15", "state": 1},
    )
    assert resp.status == HTTPStatus.BAD_REQUEST
    result = await resp.json()
    assert result == {"message": "unregistered sensor/actuator"}

    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "1", "state": 1},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}

    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer globaltoken"},
        json={"zone": "1", "state": 1},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}

    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "4", "temp": 22, "humi": 20},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}

    # Test the put endpoint for sensor updates
    resp = await client.post(
        "/api/konnected/device/112233445566",
        headers={"Authorization": "Bearer abcdefgh"},
        json={"zone": "1", "state": 1},
    )
    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"message": "ok"}