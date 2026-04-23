async def test_deprecated_firmware_issue(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_rpc_device: Mock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test repair issues handling deprecated firmware."""
    issue_id = DEPRECATED_FIRMWARE_ISSUE_ID.format(unique=MOCK_MAC)
    assert await async_setup_component(hass, "repairs", {})
    await hass.async_block_till_done()
    with patch(
        "homeassistant.components.shelly.repairs.DEPRECATED_FIRMWARES",
        {
            MODEL_WALL_DISPLAY: DeprecatedFirmwareInfo(
                {"min_firmware": "2.3.0", "ha_version": "2025.10.0"}
            )
        },
    ):
        await init_integration(hass, 2, model=MODEL_WALL_DISPLAY)

    # The default fw version in tests is 1.0.0, the repair issue should be created.
    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 1

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)

    flow_id = result["flow_id"]
    assert result["step_id"] == "confirm"

    result = await process_repair_fix_flow(client, flow_id)
    assert result["type"] == "create_entry"
    assert mock_rpc_device.trigger_ota_update.call_count == 1

    # Assert the issue is no longer present
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)
    assert len(issue_registry.issues) == 0