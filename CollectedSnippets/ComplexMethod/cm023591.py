async def test_same_topic(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    setup_tasmota,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test detecting devices with same topic."""
    configs = [
        copy.deepcopy(DEFAULT_CONFIG),
        copy.deepcopy(DEFAULT_CONFIG),
        copy.deepcopy(DEFAULT_CONFIG),
    ]
    configs[0]["rl"][0] = 1
    configs[1]["rl"][0] = 1
    configs[2]["rl"][0] = 1
    configs[0]["mac"] = "000000000001"
    configs[1]["mac"] = "000000000002"
    configs[2]["mac"] = "000000000003"

    for config in configs[0:2]:
        async_fire_mqtt_message(
            hass,
            f"{DEFAULT_PREFIX}/{config['mac']}/config",
            json.dumps(config),
        )
    await hass.async_block_till_done()

    # Verify device registry entries are created for both devices
    for config in configs[0:2]:
        device_entry = device_registry.async_get_device(
            connections={(dr.CONNECTION_NETWORK_MAC, config["mac"])}
        )
        assert device_entry is not None
        assert device_entry.configuration_url == f"http://{config['ip']}/"
        assert device_entry.manufacturer == "Tasmota"
        assert device_entry.model == config["md"]
        assert device_entry.name == config["dn"]
        assert device_entry.sw_version == config["sw"]

    # Verify entities are created only for the first device
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, configs[0]["mac"])}
    )
    assert len(er.async_entries_for_device(entity_registry, device_entry.id, True)) == 1
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, configs[1]["mac"])}
    )
    assert len(er.async_entries_for_device(entity_registry, device_entry.id, True)) == 0

    # Verify a repairs issue was created
    issue_id = "topic_duplicated_tasmota_49A3BC/cmnd/"
    issue = issue_registry.async_get_issue("tasmota", issue_id)
    assert issue.data["mac"] == " ".join(config["mac"] for config in configs[0:2])

    # Discover a 3rd device with same topic
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{configs[2]['mac']}/config",
        json.dumps(configs[2]),
    )
    await hass.async_block_till_done()

    # Verify device registry entries was created
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, configs[2]["mac"])}
    )
    assert device_entry is not None
    assert device_entry.configuration_url == f"http://{configs[2]['ip']}/"
    assert device_entry.manufacturer == "Tasmota"
    assert device_entry.model == configs[2]["md"]
    assert device_entry.name == configs[2]["dn"]
    assert device_entry.sw_version == configs[2]["sw"]

    # Verify no entities were created
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, configs[2]["mac"])}
    )
    assert len(er.async_entries_for_device(entity_registry, device_entry.id, True)) == 0

    # Verify the repairs issue has been updated
    issue = issue_registry.async_get_issue("tasmota", issue_id)
    assert issue.data["mac"] == " ".join(config["mac"] for config in configs[0:3])

    # Rediscover 3rd device with fixed config
    configs[2]["t"] = "unique_topic_2"
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{configs[2]['mac']}/config",
        json.dumps(configs[2]),
    )
    await hass.async_block_till_done()

    # Verify entities are created also for the third device
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, configs[2]["mac"])}
    )
    assert len(er.async_entries_for_device(entity_registry, device_entry.id, True)) == 1

    # Verify the repairs issue has been updated
    issue = issue_registry.async_get_issue("tasmota", issue_id)
    assert issue.data["mac"] == " ".join(config["mac"] for config in configs[0:2])

    # Rediscover 2nd device with fixed config
    configs[1]["t"] = "unique_topic_1"
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{configs[1]['mac']}/config",
        json.dumps(configs[1]),
    )
    await hass.async_block_till_done()

    # Verify entities are created also for the second device
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, configs[1]["mac"])}
    )
    assert len(er.async_entries_for_device(entity_registry, device_entry.id, True)) == 1

    # Verify the repairs issue has been removed
    assert issue_registry.async_get_issue("tasmota", issue_id) is None