async def test_get_services(
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get_services command."""
    assert ALL_SERVICE_DESCRIPTIONS_JSON_CACHE not in hass.data
    await websocket_client.send_json_auto_id({"type": "get_services"})
    msg = await websocket_client.receive_json()
    assert msg == {"id": 1, "result": {}, "success": True, "type": "result"}

    # Check cache is reused
    old_cache = hass.data[ALL_SERVICE_DESCRIPTIONS_JSON_CACHE]
    await websocket_client.send_json_auto_id({"type": "get_services"})
    msg = await websocket_client.receive_json()
    assert msg == {"id": 2, "result": {}, "success": True, "type": "result"}
    assert hass.data[ALL_SERVICE_DESCRIPTIONS_JSON_CACHE] is old_cache

    # Set up an integration that has services and check cache is updated
    assert await async_setup_component(hass, GROUP_DOMAIN, {GROUP_DOMAIN: {}})
    await websocket_client.send_json_auto_id({"type": "get_services"})
    msg = await websocket_client.receive_json()
    assert msg == {
        "id": 3,
        "result": {GROUP_DOMAIN: ANY},
        "success": True,
        "type": "result",
    }
    group_services = msg["result"][GROUP_DOMAIN]
    assert group_services == snapshot
    assert hass.data[ALL_SERVICE_DESCRIPTIONS_JSON_CACHE] is not old_cache

    # Check cache is reused
    old_cache = hass.data[ALL_SERVICE_DESCRIPTIONS_JSON_CACHE]
    await websocket_client.send_json_auto_id({"type": "get_services"})
    msg = await websocket_client.receive_json()
    assert msg == {
        "id": 4,
        "result": {GROUP_DOMAIN: group_services},
        "success": True,
        "type": "result",
    }
    assert hass.data[ALL_SERVICE_DESCRIPTIONS_JSON_CACHE] is old_cache

    # Set up an integration with legacy translations in services.yaml
    def _load_services_file(integration: Integration) -> JSON_TYPE:
        return {
            "set_default_level": {
                "description": "Translated description",
                "fields": {
                    "level": {
                        "description": "Field description",
                        "example": "Field example",
                        "name": "Field name",
                        "selector": {
                            "select": {
                                "options": [
                                    "debug",
                                    "info",
                                    "warning",
                                    "error",
                                    "fatal",
                                    "critical",
                                ],
                                "translation_key": "level",
                            }
                        },
                    }
                },
                "name": "Translated name",
            },
            "set_level": None,
        }

    await async_setup_component(hass, LOGGER_DOMAIN, {LOGGER_DOMAIN: {}})
    await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.helpers.service._load_services_file",
            side_effect=_load_services_file,
        ),
    ):
        await websocket_client.send_json_auto_id({"type": "get_services"})
        msg = await websocket_client.receive_json()

    assert msg == {
        "id": 5,
        "result": {
            LOGGER_DOMAIN: ANY,
            GROUP_DOMAIN: group_services,
        },
        "success": True,
        "type": "result",
    }
    logger_services = msg["result"][LOGGER_DOMAIN]
    assert logger_services == snapshot