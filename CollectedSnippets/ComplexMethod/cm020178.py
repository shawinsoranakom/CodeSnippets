async def test_supervisor_issues_add_remove(
    hass: HomeAssistant,
    supervisor_client: AsyncMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test supervisor issues added and removed from dispatches."""
    mock_resolution_info(supervisor_client)

    result = await async_setup_component(hass, "hassio", {})
    assert result

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "issue_changed",
                "data": {
                    "uuid": (issue_uuid := uuid4().hex),
                    "type": "reboot_required",
                    "context": "system",
                    "reference": None,
                    "suggestions": [
                        {
                            "uuid": uuid4().hex,
                            "type": "execute_reboot",
                            "context": "system",
                            "reference": None,
                        }
                    ],
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
    assert_issue_repair_in_list(
        msg["result"]["issues"],
        uuid=issue_uuid,
        context="system",
        type_="reboot_required",
        fixable=True,
        reference=None,
    )

    await client.send_json(
        {
            "id": 3,
            "type": "supervisor/event",
            "data": {
                "event": "issue_removed",
                "data": {
                    "uuid": issue_uuid,
                    "type": "reboot_required",
                    "context": "system",
                    "reference": None,
                },
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