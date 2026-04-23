async def test_subentry_options_thinking_budget_more_than_max(
    hass: HomeAssistant, mock_config_entry, mock_init_component
) -> None:
    """Test error about thinking budget being more than max tokens."""
    subentry = next(iter(mock_config_entry.subentries.values()))
    options = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )

    # Configure initial step
    options = await hass.config_entries.subentries.async_configure(
        options["flow_id"],
        {
            "prompt": "Speak like a pirate",
            "recommended": False,
        },
    )
    assert options["type"] is FlowResultType.FORM
    assert options["step_id"] == "advanced"

    # Configure advanced step
    options = await hass.config_entries.subentries.async_configure(
        options["flow_id"],
        {"chat_model": "claude-sonnet-4-5"},
    )
    assert options["type"] is FlowResultType.FORM
    assert options["step_id"] == "model"

    # Configure model step
    options = await hass.config_entries.subentries.async_configure(
        options["flow_id"],
        {
            "max_tokens": 8192,
            "thinking_budget": 16384,
        },
    )
    await hass.async_block_till_done()
    assert options["type"] is FlowResultType.FORM
    assert options["errors"] == {"thinking_budget": "thinking_budget_too_large"}

    # Try again
    options = await hass.config_entries.subentries.async_configure(
        options["flow_id"],
        {
            "max_tokens": 16384,
            "thinking_budget": 8192,
        },
    )
    await hass.async_block_till_done()
    assert options["type"] is FlowResultType.ABORT
    assert options["reason"] == "reconfigure_successful"
    assert subentry.data["max_tokens"] == 16384
    assert subentry.data["thinking_budget"] == 8192