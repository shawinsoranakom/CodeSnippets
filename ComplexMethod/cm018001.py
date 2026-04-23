async def test_setup_raise_not_ready(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a setup raising not ready."""
    entry = MockConfigEntry(title="test_title", domain="test")
    entry.add_to_hass(hass)

    mock_setup_entry = AsyncMock(
        side_effect=ConfigEntryNotReady("The internet connection is offline")
    )
    mock_integration(hass, MockModule("test", async_setup_entry=mock_setup_entry))
    mock_platform(hass, "test.config_flow", None)

    with patch("homeassistant.config_entries.async_call_later") as mock_call:
        await manager.async_setup(entry.entry_id)

    assert len(mock_call.mock_calls) == 1
    assert (
        "Config entry 'test_title' for test integration not ready yet:"
        " The internet connection is offline"
    ) in caplog.text

    p_hass, p_wait_time, p_setup = mock_call.mock_calls[0][1]

    assert p_hass is hass
    assert 5 <= p_wait_time <= 5.5
    assert entry.state is config_entries.ConfigEntryState.SETUP_RETRY
    assert entry.reason == "The internet connection is offline"

    mock_setup_entry.side_effect = None
    mock_setup_entry.return_value = True

    hass.async_run_hass_job(p_setup, None)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert entry.reason is None