async def test_module_log_level_override(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, hass_admin_user: MockUser
) -> None:
    """Test override yaml integration log level."""
    websocket_client = await hass_ws_client()
    assert await async_setup_component(
        hass,
        "logger",
        {"logger": {"logs": {"homeassistant.components.websocket_api": "warning"}}},
    )

    assert hass.data[DATA_LOGGER].overrides == {
        "homeassistant.components.websocket_api": logging.WARNING
    }

    await websocket_client.send_json(
        {
            "id": 6,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "ERROR",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert hass.data[DATA_LOGGER].overrides == {
        "homeassistant.components.websocket_api": logging.ERROR
    }

    await websocket_client.send_json(
        {
            "id": 7,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "DEBUG",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert hass.data[DATA_LOGGER].overrides == {
        "homeassistant.components.websocket_api": logging.DEBUG
    }

    await websocket_client.send_json(
        {
            "id": 8,
            "type": "logger/log_level",
            "module": "homeassistant.components.websocket_api",
            "level": "NOTSET",
            "persistence": "none",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 8
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]

    assert hass.data[DATA_LOGGER].overrides == {
        "homeassistant.components.websocket_api": logging.NOTSET
    }