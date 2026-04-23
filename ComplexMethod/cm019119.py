async def test_websocket_get_trigger_capabilities(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    fake_integration,
    trigger_key: str,
) -> None:
    """Test we get the expected trigger capabilities through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )
    expected_capabilities = {
        "extra_fields": [
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ]
    }

    async def _async_get_trigger_capabilities(
        hass: HomeAssistant, config: ConfigType
    ) -> dict[str, vol.Schema]:
        """List trigger capabilities."""
        return await toggle_entity.async_get_trigger_capabilities(hass, config)

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_get_trigger_capabilities = _async_get_trigger_capabilities

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/trigger/list",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    triggers: dict = msg["result"]

    msg_id = 2
    assert len(triggers) == 3  # toggled, turned_on, turned_off
    for trigger in triggers:
        trigger[trigger_key] = trigger.pop("platform")
        await client.send_json(
            {
                "id": msg_id,
                "type": "device_automation/trigger/capabilities",
                "trigger": trigger,
            }
        )
        msg = await client.receive_json()
        assert msg["id"] == msg_id
        assert msg["type"] == TYPE_RESULT
        assert msg["success"]
        capabilities = msg["result"]
        assert capabilities == expected_capabilities
        msg_id = msg_id + 1