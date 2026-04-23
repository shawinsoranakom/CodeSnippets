async def test_create_conversation_agent_web_search(
    hass: HomeAssistant,
    mock_open_router_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    web_search: bool,
    expected_web_search: bool,
) -> None:
    """Test creating a conversation agent with web search enabled/disabled."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Verify web_search field is present in schema with correct default
    schema = result["data_schema"].schema
    key = next(k for k in schema if k == CONF_WEB_SEARCH)
    assert key.default() is False

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "openai/gpt-3.5-turbo",
            CONF_PROMPT: "you are an assistant",
            CONF_LLM_HASS_API: ["assist"],
            CONF_WEB_SEARCH: expected_web_search,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_WEB_SEARCH] is expected_web_search