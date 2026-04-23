async def test_reauth_helper_alignment(
    hass: HomeAssistant,
    manager: config_entries.ConfigEntries,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test `start_reauth_flow` helper alignment.

    It should be aligned with `ConfigEntry._async_init_reauth`.
    """
    entry = MockConfigEntry(
        title="test_title",
        domain="test",
        entry_id="01J915Q6T9F6G5V0QJX6HBC94T",
        data={"host": "any", "port": 123},
        unique_id=None,
    )
    entry.add_to_hass(hass)

    mock_setup_entry = AsyncMock(
        side_effect=ConfigEntryAuthFailed("The password is no longer valid")
    )
    mock_integration(hass, MockModule("test", async_setup_entry=mock_setup_entry))
    mock_platform(hass, "test.config_flow", None)

    # Check context via auto-generated reauth
    await manager.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert "could not authenticate: The password is no longer valid" in caplog.text

    assert entry.state is config_entries.ConfigEntryState.SETUP_ERROR
    assert entry.reason == "The password is no longer valid"

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    reauth_flow_context = flows[0]["context"]
    reauth_flow_init_data = hass.config_entries.flow._progress[
        flows[0]["flow_id"]
    ].init_data

    # Clear to make way for `start_reauth_flow` helper
    manager.flow.async_abort(flows[0]["flow_id"])
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 0

    # Check context via `start_reauth_flow` helper
    await entry.start_reauth_flow(hass)
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    helper_flow_context = flows[0]["context"]
    helper_flow_init_data = hass.config_entries.flow._progress[
        flows[0]["flow_id"]
    ].init_data

    # Ensure context and init data are aligned
    assert helper_flow_context == reauth_flow_context
    assert helper_flow_init_data == reauth_flow_init_data