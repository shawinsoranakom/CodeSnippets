async def test_google_entity_sync_serialize_with_local_sdk(hass: HomeAssistant) -> None:
    """Test sync serialize attributes of a GoogleEntity."""
    hass.states.async_set("light.ceiling_lights", "off")
    hass.config.api = Mock(port=1234, local_ip="192.168.123.123", use_ssl=False)
    await async_process_ha_core_config(
        hass,
        {"external_url": "https://hostname:1234"},
    )

    hass.http = Mock(server_port=1234)
    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
    )
    entity = helpers.GoogleEntity(hass, config, hass.states.get("light.ceiling_lights"))

    serialized = entity.sync_serialize(None, "mock-uuid")
    assert "otherDeviceIds" not in serialized
    assert "customData" not in serialized

    config.async_enable_local_sdk()

    serialized = entity.sync_serialize("mock-user-id", "abcdef")
    assert serialized["otherDeviceIds"] == [{"deviceId": "light.ceiling_lights"}]
    assert serialized["customData"] == {
        "httpPort": 1234,
        "webhookId": "mock-webhook-id",
        "uuid": "abcdef",
    }

    for device_type in NOT_EXPOSE_LOCAL:
        with patch(
            "homeassistant.components.google_assistant.helpers.get_google_type",
            return_value=device_type,
        ):
            serialized = entity.sync_serialize(None, "mock-uuid")
            assert "otherDeviceIds" not in serialized
            assert "customData" not in serialized