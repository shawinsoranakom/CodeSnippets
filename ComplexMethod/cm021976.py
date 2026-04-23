async def test_subentry_web_search_user_location(
    hass: HomeAssistant, mock_config_entry, mock_init_component
) -> None:
    """Test fetching user location."""
    subentry = next(iter(mock_config_entry.subentries.values()))
    options_flow = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )

    # Configure initial step
    options = await hass.config_entries.subentries.async_configure(
        options_flow["flow_id"],
        {
            "prompt": "You are a helpful assistant",
            "recommended": False,
        },
    )
    assert options["type"] is FlowResultType.FORM
    assert options["step_id"] == "advanced"

    # Configure advanced step
    options = await hass.config_entries.subentries.async_configure(
        options["flow_id"],
        {
            "chat_model": "claude-sonnet-4-5",
        },
    )
    assert options["type"] is FlowResultType.FORM
    assert options["step_id"] == "model"

    hass.config.country = "US"
    hass.config.time_zone = "America/Los_Angeles"
    hass.states.async_set(
        "zone.home", "0", {"latitude": 37.7749, "longitude": -122.4194}
    )

    with patch(
        "anthropic.resources.messages.AsyncMessages.create",
        new_callable=AsyncMock,
        return_value=types.Message(
            type="message",
            id="mock_message_id",
            role="assistant",
            model="claude-sonnet-4-0",
            usage=types.Usage(input_tokens=100, output_tokens=100),
            content=[
                types.TextBlock(
                    type="text",
                    text='{"city": "San Francisco", "region": "California"}',
                )
            ],
        ),
    ) as mock_create:
        # Configure model step
        options = await hass.config_entries.subentries.async_configure(
            options["flow_id"],
            {
                "max_tokens": 8192,
                "web_search": True,
                "web_search_max_uses": 5,
                "user_location": True,
            },
        )

    assert (
        mock_create.call_args.kwargs["messages"][0]["content"] == "Where are the "
        "following coordinates located: (37.7749, -122.4194)?"
    )
    assert options["type"] is FlowResultType.ABORT
    assert options["reason"] == "reconfigure_successful"
    assert subentry.data == {
        "chat_model": "claude-sonnet-4-5",
        "city": "San Francisco",
        "country": "US",
        "max_tokens": 8192,
        "prompt": "You are a helpful assistant",
        "prompt_caching": "prompt",
        "recommended": False,
        "region": "California",
        "thinking_budget": 1024,
        "timezone": "America/Los_Angeles",
        "tool_search": False,
        "user_location": True,
        "web_search": True,
        "web_search_max_uses": 5,
        "code_execution": False,
    }