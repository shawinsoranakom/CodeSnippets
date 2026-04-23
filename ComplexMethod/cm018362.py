async def test_subentry_web_search_user_location(
    hass: HomeAssistant,
    mock_config_entry,
    mock_init_component,
    store_responses: bool,
) -> None:
    """Test fetching user location."""
    subentry = next(
        sub
        for sub in mock_config_entry.subentries.values()
        if sub.subentry_type == "conversation"
    )
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
        },
    )
    assert subentry_flow["type"] is FlowResultType.FORM
    assert subentry_flow["step_id"] == "advanced"

    # Configure advanced step
    subentry_flow = await hass.config_entries.subentries.async_configure(
        subentry_flow["flow_id"],
        {
            CONF_TEMPERATURE: 1.0,
            CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
            CONF_TOP_P: RECOMMENDED_TOP_P,
            CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
            CONF_STORE_RESPONSES: store_responses,
        },
    )
    await hass.async_block_till_done()
    assert subentry_flow["type"] is FlowResultType.FORM
    assert subentry_flow["step_id"] == "model"

    hass.config.country = "US"
    hass.config.time_zone = "America/Los_Angeles"
    hass.states.async_set(
        "zone.home", "0", {"latitude": 37.7749, "longitude": -122.4194}
    )
    with patch(
        "openai.resources.responses.AsyncResponses.create",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = Response(
            object="response",
            id="resp_A",
            created_at=1700000000,
            model="gpt-4o-mini",
            parallel_tool_calls=True,
            tool_choice="auto",
            tools=[],
            output=[
                ResponseOutputMessage(
                    type="message",
                    id="msg_A",
                    content=[
                        ResponseOutputText(
                            type="output_text",
                            text='{"city": "San Francisco", "region": "California"}',
                            annotations=[],
                        )
                    ],
                    role="assistant",
                    status="completed",
                )
            ],
        )

        # Configure model step
        subentry_flow = await hass.config_entries.subentries.async_configure(
            subentry_flow["flow_id"],
            {
                CONF_WEB_SEARCH: True,
                CONF_WEB_SEARCH_CONTEXT_SIZE: "medium",
                CONF_WEB_SEARCH_USER_LOCATION: True,
            },
        )
        await hass.async_block_till_done()
    assert (
        mock_create.call_args.kwargs["input"][0]["content"] == "Where are the following"
        " coordinates located: (37.7749, -122.4194)?"
    )
    assert mock_create.call_args.kwargs["store"] is store_responses
    assert subentry_flow["type"] is FlowResultType.ABORT
    assert subentry_flow["reason"] == "reconfigure_successful"
    assert subentry.data == {
        CONF_RECOMMENDED: False,
        CONF_PROMPT: "Speak like a pirate",
        CONF_TEMPERATURE: 1.0,
        CONF_CHAT_MODEL: RECOMMENDED_CHAT_MODEL,
        CONF_TOP_P: RECOMMENDED_TOP_P,
        CONF_MAX_TOKENS: RECOMMENDED_MAX_TOKENS,
        CONF_SERVICE_TIER: "auto",
        CONF_STORE_RESPONSES: store_responses,
        CONF_WEB_SEARCH: True,
        CONF_WEB_SEARCH_CONTEXT_SIZE: "medium",
        CONF_WEB_SEARCH_USER_LOCATION: True,
        CONF_WEB_SEARCH_CITY: "San Francisco",
        CONF_WEB_SEARCH_REGION: "California",
        CONF_WEB_SEARCH_COUNTRY: "US",
        CONF_WEB_SEARCH_TIMEZONE: "America/Los_Angeles",
        CONF_WEB_SEARCH_INLINE_CITATIONS: False,
        CONF_CODE_INTERPRETER: False,
    }