async def test_unhealthy_issues_add_remove(
    hass: HomeAssistant,
    supervisor_client: AsyncMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test unhealthy issues added and removed from dispatches."""
    mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    assert result

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "health_changed",
                "data": {
                    "healthy": False,
                    "unhealthy_reasons": ["docker"],
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    await client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert len(msg["result"]["issues"]) == 1
    assert_repair_in_list(msg["result"]["issues"], unhealthy=True, reason="docker")

    await client.send_json(
        {
            "id": 3,
            "type": "supervisor/event",
            "data": {
                "event": "health_changed",
                "data": {"healthy": True},
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    await client.send_json({"id": 4, "type": "repairs/list_issues"})
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] == {"issues": []}