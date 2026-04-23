async def test_duplicate_repair_issue_repair_flow(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test desired flow of the fix flow for duplicate instance ID."""
    assert await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})
    assert await async_setup_component(hass, HOMEASSISTANT_DOMAIN, {})
    await async_process_repairs_platforms(hass)

    with (
        patch("homeassistant.helpers.instance_id.async_get", return_value="abc123"),
        patch.object(discovery, "AsyncServiceBrowser", side_effect=service_update_mock),
        patch.object(hass.config_entries.flow, "async_init"),
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceInfo",
            side_effect=_get_hass_service_info_mock,
        ),
        patch.object(
            instance_id, "async_recreate", return_value="new-uuid"
        ) as mock_recreate,
        patch("homeassistant.config.async_check_ha_config_file", return_value=None),
        patch("homeassistant.core.HomeAssistant.async_stop", return_value=None),
    ):
        assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()

        issue = issue_registry.async_get_issue(
            domain="zeroconf", issue_id="duplicate_instance_id"
        )
        assert issue is not None

        client = await hass_client()

        result = await start_repair_fix_flow(client, DOMAIN, issue.issue_id)

        flow_id = result["flow_id"]
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "confirm_recreate"

        result = await process_repair_fix_flow(client, flow_id, json={})
        assert result["type"] == "create_entry"

        await hass.async_block_till_done()

        assert mock_recreate.called