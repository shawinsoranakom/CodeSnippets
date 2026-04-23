async def test_creating_ai_task_subentry_advanced(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
) -> None:
    """Test creating an AI task subentry with advanced settings."""
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "ai_task_data"),
        context={"source": config_entries.SOURCE_USER},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "init"

    # Go to advanced settings
    result2 = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Advanced AI Task",
            CONF_RECOMMENDED: False,
        },
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "advanced"

    # Configure advanced settings
    result3 = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_CHAT_MODEL: "claude-sonnet-4-5",
        },
    )

    assert result3.get("type") is FlowResultType.FORM
    assert result3.get("step_id") == "model"

    # Configure model settings
    result4 = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MAX_TOKENS: 1200,
            CONF_WEB_SEARCH: False,
        },
    )

    assert result4.get("type") is FlowResultType.CREATE_ENTRY
    assert result4.get("title") == "Advanced AI Task"
    assert result4.get("data") == {
        CONF_RECOMMENDED: False,
        CONF_CHAT_MODEL: "claude-sonnet-4-5",
        CONF_MAX_TOKENS: 1200,
        CONF_TOOL_SEARCH: False,
        CONF_WEB_SEARCH: False,
        CONF_WEB_SEARCH_MAX_USES: 5,
        CONF_WEB_SEARCH_USER_LOCATION: False,
        CONF_THINKING_BUDGET: 1024,
        CONF_CODE_EXECUTION: False,
        CONF_PROMPT_CACHING: "prompt",
    }