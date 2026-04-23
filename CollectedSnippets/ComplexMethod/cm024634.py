async def test_event_topic_protected(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_aiontfy: AsyncMock,
    freezer: FrozenDateTimeFactory,
    issue_registry: ir.IssueRegistry,
    entity_registry: er.EntityRegistry,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test ntfy events cannot subscribe to protected topic."""
    mock_aiontfy.subscribe.side_effect = NtfyForbiddenError(403, 403, "forbidden")

    config_entry.add_to_hass(hass)
    assert await async_setup_component(hass, "repairs", {})
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    freezer.tick(timedelta(seconds=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("event.mytopic"))
    assert state.state == STATE_UNAVAILABLE

    assert issue_registry.async_get_issue(
        domain=DOMAIN, issue_id="topic_protected_mytopic"
    )

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, "topic_protected_mytopic")

    flow_id = result["flow_id"]
    assert result["step_id"] == "confirm"

    result = await process_repair_fix_flow(client, flow_id)
    assert result["type"] == "create_entry"

    assert (entity := entity_registry.async_get("event.mytopic"))
    assert entity.disabled
    assert entity.disabled_by is er.RegistryEntryDisabler.USER