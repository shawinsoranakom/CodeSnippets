async def test_assist_api_tools_conversion(
    hass: HomeAssistant,
    mock_config_entry_with_assist: MockConfigEntry,
    mock_init_component,
    mock_create_stream,
) -> None:
    """Test that we are able to convert actual tools from Assist API."""
    for component in (
        "calendar",
        "climate",
        "cover",
        "humidifier",
        "intent",
        "light",
        "media_player",
        "script",
        "shopping_list",
        "todo",
        "vacuum",
        "weather",
    ):
        assert await async_setup_component(hass, component, {})
        hass.states.async_set(f"{component}.test", "on")
        async_expose_entity(hass, "conversation", f"{component}.test", True)

    async_register_timer_handler(hass, "test_device", lambda *args: None)

    mock_create_stream.return_value = [
        create_message_item(id="msg_A", text="Cool", output_index=0)
    ]

    await conversation.async_converse(
        hass,
        "hello",
        None,
        Context(),
        agent_id="conversation.openai_conversation",
        device_id="test_device",
    )

    tools = mock_create_stream.mock_calls[0][2]["tools"]
    assert tools

    for tool in tools:
        msg = (
            f"Invalid schema for function '{tool['name']}': schema must have type "
            "'object' and not have 'oneOf'/'anyOf'/'allOf'/'enum'/'not' at the top level."
        )
        assert tool["parameters"]["type"] == "object", msg
        for key in ("oneOf", "anyOf", "allOf", "enum", "not"):
            assert key not in tool["parameters"], msg