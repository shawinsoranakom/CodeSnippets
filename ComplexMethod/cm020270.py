async def test_reconfigure_conversation_agent(
    hass: HomeAssistant,
    mock_open_router_client: AsyncMock,
    mock_openai_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguring a conversation agent."""
    await setup_integration(hass, mock_config_entry)

    subentry_id = get_subentry_id(mock_config_entry, "conversation")

    # Now reconfigure it
    result = await mock_config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Update the configuration
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "openai/gpt-4",
            CONF_PROMPT: "updated prompt",
            CONF_LLM_HASS_API: ["assist"],
            CONF_WEB_SEARCH: True,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    subentry = mock_config_entry.subentries[subentry_id]
    assert subentry.data[CONF_MODEL] == "openai/gpt-4"
    assert subentry.data[CONF_PROMPT] == "updated prompt"
    assert subentry.data[CONF_LLM_HASS_API] == ["assist"]
    assert subentry.data[CONF_WEB_SEARCH] is True