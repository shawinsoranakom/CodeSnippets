async def test_extra_systen_prompt(
    hass: HomeAssistant, mock_conversation_input: ConversationInput
) -> None:
    """Test that extra system prompt works."""
    extra_system_prompt = "Garage door cover.garage_door has been left open for 30 minutes. We asked the user if they want to close it."
    extra_system_prompt2 = (
        "User person.paulus came home. Asked him what he wants to do."
    )
    mock_conversation_input.extra_system_prompt = extra_system_prompt

    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="mock-agent-id",
                content="Hey!",
            )
        )

    assert chat_log.extra_system_prompt == extra_system_prompt
    assert chat_log.content[0].content.endswith(extra_system_prompt)

    # Verify that follow-up conversations with no system prompt take previous one
    conversation_id = chat_log.conversation_id
    mock_conversation_input.extra_system_prompt = None

    with (
        chat_session.async_get_chat_session(hass, conversation_id) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )

    assert chat_log.extra_system_prompt == extra_system_prompt
    assert chat_log.content[0].content.endswith(extra_system_prompt)

    # Verify that we take new system prompts
    mock_conversation_input.extra_system_prompt = extra_system_prompt2

    with (
        chat_session.async_get_chat_session(hass, conversation_id) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id="mock-agent-id",
                content="Hey!",
            )
        )

    assert chat_log.extra_system_prompt == extra_system_prompt2
    assert chat_log.content[0].content.endswith(extra_system_prompt2)
    assert extra_system_prompt not in chat_log.content[0].content

    # Verify that follow-up conversations with no system prompt take previous one
    mock_conversation_input.extra_system_prompt = None

    with (
        chat_session.async_get_chat_session(hass, conversation_id) as session,
        async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
    ):
        await chat_log.async_provide_llm_data(
            mock_conversation_input.as_llm_context("test"),
            user_llm_hass_api=None,
            user_llm_prompt=None,
            user_extra_system_prompt=mock_conversation_input.extra_system_prompt,
        )

    assert chat_log.extra_system_prompt == extra_system_prompt2
    assert chat_log.content[0].content.endswith(extra_system_prompt2)