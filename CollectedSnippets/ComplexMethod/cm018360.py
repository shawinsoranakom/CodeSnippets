async def test_subentry_unsupported_reasoning_effort(
    hass: HomeAssistant, mock_config_entry, mock_init_component, parameter, error
) -> None:
    """Test the subentry form giving error about unsupported minimal reasoning effort."""
    subentry = next(iter(mock_config_entry.subentries.values()))
    subentry_flow = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )
    assert subentry_flow["type"] is FlowResultType.FORM
    assert subentry_flow["step_id"] == "init"

    # Configure initial step
    subentry_flow = await hass.config_entries.subentries.async_configure(
        subentry_flow["flow_id"],
        {
            CONF_RECOMMENDED: False,
            CONF_PROMPT: "Speak like a pirate",
            CONF_LLM_HASS_API: ["assist"],
        },
    )
    assert subentry_flow["type"] is FlowResultType.FORM
    assert subentry_flow["step_id"] == "advanced"

    # Configure advanced step
    subentry_flow = await hass.config_entries.subentries.async_configure(
        subentry_flow["flow_id"],
        {
            CONF_CHAT_MODEL: "gpt-5",
        },
    )
    assert subentry_flow["type"] is FlowResultType.FORM
    assert subentry_flow["step_id"] == "model"

    # Configure model step
    subentry_flow = await hass.config_entries.subentries.async_configure(
        subentry_flow["flow_id"],
        {
            CONF_REASONING_EFFORT: "minimal",
            parameter: True,
        },
    )
    assert subentry_flow["type"] is FlowResultType.FORM
    assert subentry_flow["errors"] == {parameter: error}

    # Reconfigure model step
    subentry_flow = await hass.config_entries.subentries.async_configure(
        subentry_flow["flow_id"],
        {
            CONF_REASONING_EFFORT: "low",
            parameter: True,
        },
    )
    assert subentry_flow["type"] is FlowResultType.ABORT
    assert subentry_flow["reason"] == "reconfigure_successful"