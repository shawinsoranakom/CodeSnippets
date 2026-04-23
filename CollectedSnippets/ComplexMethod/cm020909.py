async def test_device_client_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry_factory: ConfigEntryFactoryType,
    mock_websocket_message: WebsocketMessageMock,
    client_payload: dict[str, Any],
) -> None:
    """Verify that WLAN client sensors are working as expected."""
    client_payload += [
        {
            "hostname": "Wired client 1",
            "is_wired": True,
            "mac": "00:00:00:00:00:01",
            "oui": "Producer",
            "sw_mac": "01:00:00:00:00:00",
            "last_seen": dt_util.as_timestamp(dt_util.utcnow()),
        },
        {
            "hostname": "Wired client 2",
            "is_wired": True,
            "mac": "00:00:00:00:00:02",
            "oui": "Producer",
            "sw_mac": "01:00:00:00:00:00",
            "last_seen": dt_util.as_timestamp(dt_util.utcnow()),
        },
        {
            "is_wired": False,
            "mac": "00:00:00:00:00:03",
            "name": "Wireless client 1",
            "oui": "Producer",
            "ap_mac": "02:00:00:00:00:00",
            "sw_mac": "01:00:00:00:00:00",
            "last_seen": dt_util.as_timestamp(dt_util.utcnow()),
        },
    ]
    await config_entry_factory()

    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 4

    ent_reg_entry = entity_registry.async_get("sensor.wired_device_clients")
    assert ent_reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

    ent_reg_entry = entity_registry.async_get("sensor.wireless_device_clients")
    assert ent_reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

    # Enable entity
    entity_registry.async_update_entity(
        entity_id="sensor.wired_device_clients", disabled_by=None
    )
    entity_registry.async_update_entity(
        entity_id="sensor.wireless_device_clients", disabled_by=None
    )

    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # Validate state object
    assert len(hass.states.async_all()) == 13
    assert len(hass.states.async_entity_ids(SENSOR_DOMAIN)) == 6

    assert hass.states.get("sensor.wired_device_clients").state == "2"
    assert hass.states.get("sensor.wireless_device_clients").state == "1"

    # Verify state update - decreasing number
    wireless_client_1 = client_payload[2]
    wireless_client_1["last_seen"] = 0
    mock_websocket_message(message=MessageKey.CLIENT, data=wireless_client_1)

    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.wired_device_clients").state == "2"
    assert hass.states.get("sensor.wireless_device_clients").state == "0"