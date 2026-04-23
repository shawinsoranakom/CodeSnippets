async def test_update_entry_and_reload(
    hass: HomeAssistant,
    source: str,
    reason: str,
    expected_title: str,
    expected_unique_id: str,
    expected_data: dict[str, Any],
    expected_options: dict[str, Any],
    kwargs: dict[str, Any],
    calls_entry_load_unload: tuple[int, int],
    raises: type[Exception] | None,
) -> None:
    """Test updating an entry and reloading."""
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
            return self.async_update_reload_and_abort(entry, **kwargs)

        async def async_step_reconfigure(self, data):
            """Mock Reconfigure."""
            return self.async_update_reload_and_abort(entry, **kwargs)

    err: Exception
    with mock_config_flow("comp", MockFlowHandler):
        try:
            if source == config_entries.SOURCE_REAUTH:
                result = await entry.start_reauth_flow(hass)
            elif source == config_entries.SOURCE_RECONFIGURE:
                result = await entry.start_reconfigure_flow(hass)
        except Exception as ex:  # noqa: BLE001
            err = ex

    await hass.async_block_till_done()

    assert entry.title == expected_title
    assert entry.unique_id == expected_unique_id
    assert entry.data == expected_data
    assert entry.options == expected_options
    assert entry.state == config_entries.ConfigEntryState.LOADED
    if raises:
        assert isinstance(err, raises)
    else:
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == reason
    # Assert entry was reloaded
    assert len(comp.async_setup_entry.mock_calls) == calls_entry_load_unload[0]
    assert len(comp.async_unload_entry.mock_calls) == calls_entry_load_unload[1]