async def test_inconsistent_settings_keep_new(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    config_entry: MockConfigEntry,
    mock_zigpy_connect: ControllerApplication,
    network_backup: zigpy.backups.NetworkBackup,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test inconsistent ZHA network settings: keep new settings."""

    assert await async_setup_component(hass, REPAIRS_DOMAIN, {REPAIRS_DOMAIN: {}})

    config_entry.add_to_hass(hass)

    new_state = network_backup.replace(
        network_info=network_backup.network_info.replace(pan_id=0xBBBB)
    )
    old_state = network_backup

    with patch(
        "homeassistant.components.zha.Gateway.async_initialize",
        side_effect=NetworkSettingsInconsistent(
            message="Network settings are inconsistent",
            new_state=new_state,
            old_state=old_state,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state is ConfigEntryState.SETUP_ERROR

    await hass.config_entries.async_unload(config_entry.entry_id)

    issue = issue_registry.async_get_issue(
        domain=DOMAIN,
        issue_id=ISSUE_INCONSISTENT_NETWORK_SETTINGS,
    )

    # The issue is created
    assert issue is not None

    client = await hass_client()
    resp = await client.post(
        "/api/repairs/issues/fix",
        json={"handler": DOMAIN, "issue_id": issue.issue_id},
    )

    assert resp.status == HTTPStatus.OK
    data = await resp.json()

    flow_id = data["flow_id"]
    assert data["description_placeholders"]["diff"] == "- PAN ID: `0x2DB4` → `0xBBBB`"

    mock_zigpy_connect.backups.add_backup = Mock()

    resp = await client.post(
        f"/api/repairs/issues/fix/{flow_id}",
        json={"next_step_id": "use_new_settings"},
    )
    await hass.async_block_till_done()

    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data["type"] == "create_entry"

    await hass.config_entries.async_unload(config_entry.entry_id)

    assert (
        issue_registry.async_get_issue(
            domain=DOMAIN,
            issue_id=ISSUE_INCONSISTENT_NETWORK_SETTINGS,
        )
        is None
    )

    assert mock_zigpy_connect.backups.add_backup.mock_calls == [call(new_state)]