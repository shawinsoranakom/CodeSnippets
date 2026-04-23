async def test_deprecate_entity_automation(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ufp: MockUFPFixture,
    hass_ws_client: WebSocketGenerator,
    doorbell: Camera,
) -> None:
    """Test Deprecate entity repair exists for existing installs."""
    entry = entity_registry.async_get_or_create(
        Platform.SWITCH,
        DOMAIN,
        f"{doorbell.mac}_hdr_mode",
        config_entry=ufp.entry,
    )
    await _load_automation(hass, entry.entity_id)
    await init_entry(hass, ufp, [doorbell])

    await async_process_repairs_platforms(hass)
    ws_client = await hass_ws_client(hass)

    await ws_client.send_json({"id": 1, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "deprecate_hdr_switch":
            issue = i
    assert issue is not None

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={AUTOMATION_DOMAIN: []},
    ):
        await hass.services.async_call(AUTOMATION_DOMAIN, SERVICE_RELOAD, blocking=True)

    await hass.config_entries.async_reload(ufp.entry.entry_id)
    await hass.async_block_till_done()

    await ws_client.send_json({"id": 2, "type": "repairs/list_issues"})
    msg = await ws_client.receive_json()

    assert msg["success"]
    issue = None
    for i in msg["result"]["issues"]:
        if i["issue_id"] == "deprecate_hdr_switch":
            issue = i
    assert issue is None