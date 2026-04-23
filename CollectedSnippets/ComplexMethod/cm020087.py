async def test_knx_get_base_data_command_with_project(
    hass: HomeAssistant,
    knx: KNXTestKit,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test knx/get_base_data command with loaded project."""
    await knx.setup_integration()
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "knx/get_base_data"})

    res = await client.receive_json()
    assert res["success"], res

    connection_info = res["result"]["connection_info"]
    assert connection_info["version"] is not None
    assert connection_info["connected"]
    assert connection_info["current_address"] == "0.0.0"

    project_info = res["result"]["project_info"]
    assert project_info is not None
    assert project_info["name"] == "Fixture"
    assert project_info["last_modified"] == "2023-04-30T09:04:04.4043671Z"
    assert project_info["tool_version"] == "5.7.1428.39779"