async def test_config_local_sdk(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the local SDK."""
    command_events = async_capture_events(hass, EVENT_COMMAND_RECEIVED)
    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    hass.states.async_set("light.ceiling_lights", "off")

    assert await async_setup_component(hass, "webhook", {})

    config = MockConfig(
        hass=hass,
        agent_user_ids={
            "mock-user-id": {
                STORE_GOOGLE_LOCAL_WEBHOOK_ID: "mock-webhook-id",
            },
        },
    )

    client = await hass_client()

    assert config.is_local_connected is False
    config.async_enable_local_sdk()
    assert config.is_local_connected is False

    resp = await client.post(
        "/api/webhook/mock-webhook-id",
        json={
            "inputs": [
                {
                    "context": {"locale_country": "US", "locale_language": "en"},
                    "intent": "action.devices.EXECUTE",
                    "payload": {
                        "commands": [
                            {
                                "devices": [{"id": "light.ceiling_lights"}],
                                "execution": [
                                    {
                                        "command": "action.devices.commands.OnOff",
                                        "params": {"on": True},
                                    }
                                ],
                            }
                        ],
                        "structureData": {},
                    },
                }
            ],
            "requestId": "mock-req-id",
        },
    )

    assert config.is_local_connected is True
    with patch(
        "homeassistant.components.google_assistant.helpers.utcnow",
        return_value=dt_util.utcnow() + timedelta(seconds=90),
    ):
        assert config.is_local_connected is False

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result["requestId"] == "mock-req-id"

    assert len(command_events) == 1
    assert command_events[0].context.user_id == "mock-user-id"

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].context is command_events[0].context

    config.async_disable_local_sdk()

    # Webhook is no longer active
    resp = await client.post("/api/webhook/mock-webhook-id")
    assert resp.status == HTTPStatus.OK
    assert await resp.read() == b""