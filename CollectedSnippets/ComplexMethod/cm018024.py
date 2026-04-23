async def test_update_entry_without_reload(
    hass: HomeAssistant,
    source: str,
    reason: str,
) -> None:
    """Test updating an entry without reloading."""
    entry = MockConfigEntry(
        domain="comp",
        unique_id="1234",
        title="Test",
        data={"vendor": "data"},
        options={"vendor": "options"},
    )
    entry.add_to_hass(hass)

    comp = MockModule(
        "comp",
        async_setup_entry=AsyncMock(return_value=True),
        async_unload_entry=AsyncMock(return_value=True),
    )
    mock_integration(hass, comp)
    mock_platform(hass, "comp.config_flow", None)

    await hass.config_entries.async_setup(entry.entry_id)

    class MockFlowHandler(config_entries.ConfigFlow):
        """Define a mock flow handler."""

        VERSION = 1

        async def async_step_reauth(self, data):
            """Mock Reauth."""
            return self.async_update_and_abort(
                entry,
                unique_id="5678",
                title="Updated title",
                data={"vendor": "data2"},
                options={"vendor": "options2"},
            )

        async def async_step_reconfigure(self, data):
            """Mock Reconfigure."""
            return self.async_update_and_abort(
                entry,
                unique_id="5678",
                title="Updated title",
                data={"vendor": "data2"},
                options={"vendor": "options2"},
            )

    with mock_config_flow("comp", MockFlowHandler):
        if source == config_entries.SOURCE_REAUTH:
            result = await entry.start_reauth_flow(hass)
        elif source == config_entries.SOURCE_RECONFIGURE:
            result = await entry.start_reconfigure_flow(hass)

    await hass.async_block_till_done()

    assert entry.title == "Updated title"
    assert entry.unique_id == "5678"
    assert entry.data == {"vendor": "data2"}
    assert entry.options == {"vendor": "options2"}
    assert entry.state == config_entries.ConfigEntryState.LOADED
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == reason
    # Assert entry is not reloaded
    assert len(comp.async_setup_entry.mock_calls) == 1
    assert len(comp.async_unload_entry.mock_calls) == 0