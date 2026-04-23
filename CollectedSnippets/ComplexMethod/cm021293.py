async def test_race_condition(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test race condition for unknown components."""
    config = {"rflink": {"port": "/dev/ttyABC0"}, DOMAIN: {"platform": "rflink"}}
    tmp_entity = TMP_ENTITY.format("test3")

    # setup mocking rflink module
    event_callback, _, _, _ = await mock_rflink(hass, config, DOMAIN, monkeypatch)

    # test event for new unconfigured sensor
    event_callback({"id": "test3", "sensor": "battery", "value": "ok", "unit": ""})
    event_callback({"id": "test3", "sensor": "battery", "value": "ko", "unit": ""})

    # tmp_entity added to EVENT_KEY_SENSOR
    assert tmp_entity in hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_SENSOR]["test3"]
    # tmp_entity must no be added to EVENT_KEY_COMMAND
    assert tmp_entity not in hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_COMMAND]["test3"]

    await hass.async_block_till_done()

    # test state of new sensor
    updated_sensor = hass.states.get("sensor.test3")
    assert updated_sensor

    # test state of new sensor
    new_sensor = hass.states.get(f"{DOMAIN}.test3")
    assert new_sensor
    assert new_sensor.state == "ok"

    event_callback({"id": "test3", "sensor": "battery", "value": "ko", "unit": ""})
    await hass.async_block_till_done()
    # tmp_entity must be deleted from EVENT_KEY_COMMAND
    assert tmp_entity not in hass.data[DATA_ENTITY_LOOKUP][EVENT_KEY_SENSOR]["test3"]

    # test state of new sensor
    new_sensor = hass.states.get(f"{DOMAIN}.test3")
    assert new_sensor
    assert new_sensor.state == "ko"