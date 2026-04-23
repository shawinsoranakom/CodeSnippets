async def test_http_assistant(
    hass: HomeAssistant, hass_client: ClientSessionGenerator, hass_admin_user: MockUser
) -> None:
    """Test handle intent only targets exposed entities with 'assistant' set."""

    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "intent", {})

    hass.states.async_set(
        "cover.garage_door_1", "closed", {ATTR_FRIENDLY_NAME: "Garage Door 1"}
    )
    async_mock_service(hass, "cover", SERVICE_OPEN_COVER)

    client = await hass_client()

    # Exposed
    async_expose_entity(hass, conversation.DOMAIN, "cover.garage_door_1", True)
    resp = await client.post(
        "/api/intent/handle",
        json={
            "name": "HassTurnOn",
            "data": {"name": "Garage Door 1"},
            "assistant": conversation.DOMAIN,
        },
    )
    assert resp.status == 200
    data = await resp.json()
    assert data["response_type"] == intent.IntentResponseType.ACTION_DONE.value

    # Not exposed
    async_expose_entity(hass, conversation.DOMAIN, "cover.garage_door_1", False)
    resp = await client.post(
        "/api/intent/handle",
        json={
            "name": "HassTurnOn",
            "data": {"name": "Garage Door 1"},
            "assistant": conversation.DOMAIN,
        },
    )
    assert resp.status == 200
    data = await resp.json()
    assert data["response_type"] == intent.IntentResponseType.ERROR.value
    assert data["data"]["code"] == intent.IntentResponseErrorCode.FAILED_TO_HANDLE.value

    # No assistant (exposure is irrelevant)
    resp = await client.post(
        "/api/intent/handle",
        json={"name": "HassTurnOn", "data": {"name": "Garage Door 1"}},
    )
    assert resp.status == 200
    data = await resp.json()
    assert data["response_type"] == intent.IntentResponseType.ACTION_DONE.value