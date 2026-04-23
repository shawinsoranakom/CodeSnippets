async def test_reauth(
    hass: HomeAssistant, manager: config_entries.ConfigEntries
) -> None:
    """Test the async_reauth_helper."""
    entry = MockConfigEntry(title="test_title", domain="test")
    entry.add_to_hass(hass)
    entry2 = MockConfigEntry(title="test_title", domain="test")
    entry2.add_to_hass(hass)

    mock_setup_entry = AsyncMock(return_value=True)
    mock_integration(hass, MockModule("test", async_setup_entry=mock_setup_entry))
    mock_platform(hass, "test.config_flow", None)

    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    flow = hass.config_entries.flow
    with patch.object(flow, "async_init", wraps=flow.async_init) as mock_init:
        entry.async_start_reauth(
            hass,
            context={"extra_context": "some_extra_context"},
            data={"extra_data": 1234},
        )
        await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["entry_id"] == entry.entry_id
    assert flows[0]["context"]["source"] == config_entries.SOURCE_REAUTH
    assert flows[0]["context"]["title_placeholders"] == {"name": "test_title"}
    assert flows[0]["context"]["extra_context"] == "some_extra_context"

    assert mock_init.call_args.kwargs["data"]["extra_data"] == 1234

    assert entry.entry_id != entry2.entry_id

    # Check that we can't start duplicate reauth flows
    entry.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 1

    # Check that we can't start duplicate reauth flows when the context is different
    entry.async_start_reauth(hass, {"diff": "diff"})
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 1

    # Check that we can start a reauth flow for a different entry
    entry2.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 2

    # Abort all existing flows
    for flow in hass.config_entries.flow.async_progress():
        hass.config_entries.flow.async_abort(flow["flow_id"])
    await hass.async_block_till_done()

    # Check that we can't start duplicate reauth flows
    # without blocking between flows
    entry.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    entry.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    entry.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    entry.async_start_reauth(hass, {"extra_context": "some_extra_context"})
    await hass.async_block_till_done()
    assert len(hass.config_entries.flow.async_progress()) == 1