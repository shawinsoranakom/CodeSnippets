async def test_websocket_get_action_capabilities(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    fake_integration,
) -> None:
    """Test we get the expected action capabilities through websocket."""
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
        "turn_on": {
            "extra_fields": [
                {"type": "string", "name": "code", "optional": True, "required": False}
            ]
        },
        "turn_off": {"extra_fields": []},
        "toggle": {"extra_fields": []},
    }

    async def _async_get_action_capabilities(
        hass: HomeAssistant, config: ConfigType
    ) -> dict[str, vol.Schema]:
        """List action capabilities."""
        if config["type"] == "turn_on":
            return {"extra_fields": vol.Schema({vol.Optional("code"): str})}
        return {}

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_action"]
    module.async_get_action_capabilities = _async_get_action_capabilities

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "device_automation/action/list", "device_id": device_entry.id}
    )
    msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    actions = msg["result"]

    msg_id = 2
    assert len(actions) == 3
    for action in actions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "device_automation/action/capabilities",
                "action": action,
            }
        )
        msg = await client.receive_json()
        assert msg["id"] == msg_id
        assert msg["type"] == TYPE_RESULT
        assert msg["success"]
        capabilities = msg["result"]
        assert capabilities == expected_capabilities[action["type"]]
        msg_id = msg_id + 1