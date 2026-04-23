async def test_subentry_service_tier_list(
    hass: HomeAssistant,
    mock_config_entry,
    mock_init_component,
    model,
    service_tier_options,
) -> None:
    """Test the list of service tier options."""
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
            CONF_CHAT_MODEL: model,
        },
    )
    assert subentry_flow["type"] is FlowResultType.FORM
    assert subentry_flow["step_id"] == "model"
    assert (
        subentry_flow["data_schema"].schema[CONF_SERVICE_TIER].config["options"]
        if subentry_flow["data_schema"].schema.get(CONF_SERVICE_TIER)
        else []
    ) == service_tier_options