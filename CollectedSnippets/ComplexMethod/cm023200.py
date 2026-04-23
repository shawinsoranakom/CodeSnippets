async def test_statistics_sensors_migration(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    zp3111_state,
    client,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test statistics migration sensor."""
    node = Node(client, copy.deepcopy(zp3111_state))
    client.driver.controller.nodes[node.node_id] = node

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)

    controller_base_unique_id = f"{client.driver.controller.home_id}.1.statistics"
    node_base_unique_id = f"{client.driver.controller.home_id}.22.statistics"

    # Create entity registry records for the old statistics keys
    for base_unique_id, key_map in (
        (controller_base_unique_id, CONTROLLER_STATISTICS_KEY_MAP),
        (node_base_unique_id, NODE_STATISTICS_KEY_MAP),
    ):
        # old key
        for key in key_map.values():
            entity_registry.async_get_or_create(
                "sensor", DOMAIN, f"{base_unique_id}_{key}"
            )

    # Set up integration
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Validate that entity unique ID's have changed
    for base_unique_id, key_map in (
        (controller_base_unique_id, CONTROLLER_STATISTICS_KEY_MAP),
        (node_base_unique_id, NODE_STATISTICS_KEY_MAP),
    ):
        for new_key, old_key in key_map.items():
            # If the key has changed, the old entity should not exist
            if new_key != old_key:
                assert not entity_registry.async_get_entity_id(
                    "sensor", DOMAIN, f"{base_unique_id}_{old_key}"
                )
            assert entity_registry.async_get_entity_id(
                "sensor", DOMAIN, f"{base_unique_id}_{new_key}"
            )