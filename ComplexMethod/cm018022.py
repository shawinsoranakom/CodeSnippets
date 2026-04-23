async def test_reconfigure(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test the async_reconfigure_helper."""
    entry = MockConfigEntry(title="test_title", domain="test")
    entry.add_to_hass(hass)
    entry2 = MockConfigEntry(title="test_title", domain="test")
    entry2.add_to_hass(hass)

    mock_setup_entry = AsyncMock(return_value=True)
    mock_integration(hass, MockModule("test", async_setup_entry=mock_setup_entry))
    mock_platform(hass, "test.config_flow", None)

    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    def _async_start_reconfigure(config_entry: MockConfigEntry) -> None:
        hass.async_create_task(
            manager.flow.async_init(
                config_entry.domain,
                context={
                    "source": config_entries.SOURCE_RECONFIGURE,
                    "entry_id": config_entry.entry_id,
                },
            ),
            f"config entry reconfigure {config_entry.title} "
            f"{config_entry.domain} {config_entry.entry_id}",
        )

    _async_start_reconfigure(entry)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["entry_id"] == entry.entry_id
    assert flows[0]["context"]["source"] == config_entries.SOURCE_RECONFIGURE

    assert entry.entry_id != entry2.entry_id

    # Check that we can start duplicate reconfigure flows
    # (may need revisiting)
    _async_start_reconfigure(entry)
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 2

    # Check that we can start a reconfigure flow for a different entry
    _async_start_reconfigure(entry2)
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 3

    # Abort all existing flows
    for flow in hass.config_entries.flow.async_progress():
        hass.config_entries.flow.async_abort(flow["flow_id"])
    await hass.async_block_till_done()

    # Check that we can start duplicate reconfigure flows
    # without blocking between flows
    # (may need revisiting)
    _async_start_reconfigure(entry)
    _async_start_reconfigure(entry)
    _async_start_reconfigure(entry)
    _async_start_reconfigure(entry)
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 4

    # Abort all existing flows
    for flow in hass.config_entries.flow.async_progress():
        hass.config_entries.flow.async_abort(flow["flow_id"])
    await hass.async_block_till_done()

    # Check that we can start reconfigure flows with active reauth flow
    # (may need revisiting)
    entry.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 1
    _async_start_reconfigure(entry)
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 2

    # Abort all existing flows
    for flow in hass.config_entries.flow.async_progress():
        hass.config_entries.flow.async_abort(flow["flow_id"])
    await hass.async_block_till_done()

    # Check that we can't start reauth flows with active reconfigure flow
    _async_start_reconfigure(entry)
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 1
    entry.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 1