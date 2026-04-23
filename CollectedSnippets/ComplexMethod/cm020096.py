async def test_remove_device(
    hass: HomeAssistant,
    knx: KNXTestKit,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
) -> None:
    """Test device removal."""
    assert await async_setup_component(hass, "config", {})
    await knx.setup_integration(config_store_fixture="config_store_light_switch.json")
    client = await hass_ws_client(hass)

    await knx.assert_read("1/0/21", response=True, ignore_order=True)  # test light
    await knx.assert_read("1/0/45", response=True, ignore_order=True)  # test switch

    assert hass_storage[KNX_CONFIG_STORAGE_KEY]["data"]["entities"].get("switch")
    test_device = device_registry.async_get_device(
        {(DOMAIN, "knx_vdev_4c80a564f5fe5da701ed293966d6384d")}
    )
    device_id = test_device.id
    device_entities = entity_registry.entities.get_entries_for_device_id(device_id)
    assert len(device_entities) == 1

    response = await client.remove_device(device_id, knx.mock_config_entry.entry_id)
    assert response["success"]
    assert not device_registry.async_get_device(
        {(DOMAIN, "knx_vdev_4c80a564f5fe5da701ed293966d6384d")}
    )
    assert not entity_registry.entities.get_entries_for_device_id(device_id)
    assert not hass_storage[KNX_CONFIG_STORAGE_KEY]["data"]["entities"].get("switch")