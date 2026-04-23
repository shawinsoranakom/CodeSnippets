async def test_chat_log_reuse(
    hass: HomeAssistant,
    mock_conversation_input: ConversationInput,
) -> None:
    """Test that we can reuse a chat log."""
    with (
        chat_session.async_get_chat_session(hass) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        assert chat_log.conversation_id == session.conversation_id
        assert len(chat_log.content) == 1

        with async_get_chat_log(hass, session) as chat_log2:
            assert chat_log2 is chat_log
            assert len(chat_log.content) == 1

        with async_get_chat_log(hass, session, mock_conversation_input) as chat_log2:
            assert chat_log2 is chat_log
            assert len(chat_log.content) == 2
            assert chat_log.content[1].role == "user"
            assert chat_log.content[1].content == mock_conversation_input.text