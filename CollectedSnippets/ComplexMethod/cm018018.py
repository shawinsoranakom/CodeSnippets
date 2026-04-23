async def test_setup_raise_auth_failed_from_future_coordinator_update(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a coordinator raises ConfigEntryAuthFailed in the future."""
    entry = MockConfigEntry(title="test_title", domain="test")
    entry.add_to_hass(hass)

    async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
        """Mock setup entry with a simple coordinator."""

        async def _async_update_data():
            raise ConfigEntryAuthFailed("The password is no longer valid")

        coordinator = DataUpdateCoordinator(
            hass,
            logging.getLogger(__name__),
            name="any",
            config_entry=entry,
            update_method=_async_update_data,
            update_interval=timedelta(seconds=1000),
        )

        await coordinator.async_refresh()
        return True

    mock_integration(hass, MockModule("test", async_setup_entry=async_setup_entry))
    mock_platform(hass, "test.config_flow", None)

    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert "Authentication failed while fetching" in caplog.text
    assert "The password is no longer valid" in caplog.text

    assert entry.state is config_entries.ConfigEntryState.LOADED
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["entry_id"] == entry.entry_id
    assert flows[0]["context"]["source"] == config_entries.SOURCE_REAUTH

    caplog.clear()
    entry._async_set_state(hass, config_entries.ConfigEntryState.NOT_LOADED, None)

    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert "Authentication failed while fetching" in caplog.text
    assert "The password is no longer valid" in caplog.text

    # Verify multiple ConfigEntryAuthFailed does not generate a second flow
    assert entry.state is config_entries.ConfigEntryState.LOADED
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1