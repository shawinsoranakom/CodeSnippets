async def test_topic_no_prefix(
    hass: HomeAssistant,
    mqtt_mock: MqttMockHAClient,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    setup_tasmota,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test detecting devices with same topic."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["rl"][0] = 1
    config["ft"] = "%topic%/blah/"

    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{config['mac']}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    # Verify device registry entry is created
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, config["mac"])}
    )
    assert device_entry is not None
    assert device_entry.configuration_url == f"http://{config['ip']}/"
    assert device_entry.manufacturer == "Tasmota"
    assert device_entry.model == config["md"]
    assert device_entry.name == config["dn"]
    assert device_entry.sw_version == config["sw"]

    # Verify entities are not created
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, config["mac"])}
    )
    assert len(er.async_entries_for_device(entity_registry, device_entry.id, True)) == 0

    # Verify a repairs issue was created
    issue_id = "topic_no_prefix_00000049A3BC"
    assert ("tasmota", issue_id) in issue_registry.issues

    # Rediscover device with fixed config
    config["ft"] = "%topic%/%prefix%/"
    async_fire_mqtt_message(
        hass,
        f"{DEFAULT_PREFIX}/{config['mac']}/config",
        json.dumps(config),
    )
    await hass.async_block_till_done()

    # Verify entities are created
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, config["mac"])}
    )
    assert len(er.async_entries_for_device(entity_registry, device_entry.id, True)) == 1

    # Verify the repairs issue has been removed
    assert ("tasmota", issue_id) not in issue_registry.issues