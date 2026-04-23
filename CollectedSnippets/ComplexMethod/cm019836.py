async def test_generate_with_default_settings_calls_create(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
    freezer: FrozenDateTimeFactory,
    create_backup: AsyncMock,
    create_backup_settings: dict[str, Any],
    expected_call_params: dict[str, Any],
    side_effect: Exception | None,
    last_completed_automatic_backup: str,
) -> None:
    """Test backup/generate_with_automatic_settings calls async_initiate_backup."""
    created_backup: MagicMock = create_backup.return_value[1].result().backup
    created_backup.protected = create_backup_settings["password"] is not None
    client = await hass_ws_client(hass)
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to("2024-11-13T12:01:00+01:00")
    mock_agents = await setup_backup_integration(
        hass, with_hassio=False, remote_agents=["test.remote"]
    )

    await client.send_json_auto_id(
        {"type": "backup/config/update", "create_backup": create_backup_settings}
    )
    result = await client.receive_json()
    assert result["success"]

    freezer.tick()
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (
        hass_storage[DOMAIN]["data"]["config"]["create_backup"]
        == create_backup_settings
    )
    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_attempted_automatic_backup"]
        is None
    )
    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_completed_automatic_backup"]
        is None
    )

    mock_agents["test.remote"].async_upload_backup.side_effect = side_effect
    await client.send_json_auto_id({"type": "backup/generate_with_automatic_settings"})
    result = await client.receive_json()
    assert result["success"]
    assert result["result"] == {"backup_job_id": "abc123"}

    await hass.async_block_till_done()

    create_backup.assert_called_once_with(**expected_call_params)

    freezer.tick()
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_attempted_automatic_backup"]
        == "2024-11-13T12:01:01+01:00"
    )
    assert (
        hass_storage[DOMAIN]["data"]["config"]["last_completed_automatic_backup"]
        == last_completed_automatic_backup
    )