async def test_enable_coalesce(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test enabling coalesce."""
    websocket_client = await hass_ws_client(hass)

    await websocket_client.send_json(
        {
            "id": 1,
            "type": "supported_features",
            "features": {const.FEATURE_COALESCE_MESSAGES: 1},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["id"] == 1
    assert msg["success"] is True
    send_tasks: list[asyncio.Future] = []
    ids: set[int] = set()
    start_id = 2

    for idx in range(10):
        id_ = idx + start_id
        ids.add(id_)
        send_tasks.append(websocket_client.send_json({"id": id_, "type": "ping"}))

    await asyncio.gather(*send_tasks)
    returned_ids: set[int] = set()
    for _ in range(10):
        msg = await websocket_client.receive_json()
        assert msg["type"] == "pong"
        returned_ids.add(msg["id"])

    assert ids == returned_ids

    # Now close
    send_tasks_with_close: list[asyncio.Future] = []
    start_id = 12
    for idx in range(10):
        id_ = idx + start_id
        send_tasks_with_close.append(
            websocket_client.send_json({"id": id_, "type": "ping"})
        )

    send_tasks_with_close.append(websocket_client.close())
    send_tasks_with_close.append(websocket_client.send_json({"id": 50, "type": "ping"}))

    with pytest.raises(ConnectionResetError):
        await asyncio.gather(*send_tasks_with_close)