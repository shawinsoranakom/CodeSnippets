async def test_select_entity_changing_vad_sensitivity(
    hass: HomeAssistant,
    init_select: MockConfigEntry,
) -> None:
    """Test entity tracking vad sensitivity changes."""
    config_entry = init_select  # nicer naming
    config_entry.mock_state(hass, ConfigEntryState.LOADED)

    state = hass.states.get("select.assist_pipeline_test_vad_sensitivity")
    assert state is not None
    assert state.state == VadSensitivity.DEFAULT.value

    # Change select to new sensitivity
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.assist_pipeline_test_vad_sensitivity",
            "option": VadSensitivity.AGGRESSIVE.value,
        },
        blocking=True,
    )

    state = hass.states.get("select.assist_pipeline_test_vad_sensitivity")
    assert state is not None
    assert state.state == VadSensitivity.AGGRESSIVE.value

    # Reload config entry to test selected option persists
    assert await hass.config_entries.async_forward_entry_unload(
        config_entry, Platform.SELECT
    )
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.SELECT]
    )

    state = hass.states.get("select.assist_pipeline_test_vad_sensitivity")
    assert state is not None
    assert state.state == VadSensitivity.AGGRESSIVE.value