async def test_agents_on_changed_update_success(
    hass: HomeAssistant,
    setup_dsm_with_filestation: MagicMock,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test backup agent on changed update success of coordintaor."""
    client = await hass_ws_client(hass)

    # config entry is loaded
    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]["agents"]) == 2

    # coordinator update was successful
    freezer.tick(910)  # 15 min interval + 10s
    await hass.async_block_till_done(wait_background_tasks=True)
    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]["agents"]) == 2

    # coordinator update was un-successful
    setup_dsm_with_filestation.update.side_effect = SynologyDSMRequestException(
        OSError()
    )
    freezer.tick(910)
    await hass.async_block_till_done(wait_background_tasks=True)
    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]["agents"]) == 1

    # coordinator update was successful again
    setup_dsm_with_filestation.update.side_effect = None
    freezer.tick(910)
    await hass.async_block_till_done(wait_background_tasks=True)
    await client.send_json_auto_id({"type": "backup/agents/info"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]["agents"]) == 2