async def test_prepare_chat_for_generation_appends_attachments(
    hass: HomeAssistant,
    cloud_entity: BaseCloudLLMEntity,
    mock_prepare_files_for_prompt: AsyncMock,
) -> None:
    """Test chat preparation adds LLM tools, attachments, and metadata."""
    chat_log = conversation.ChatLog(hass, "conversation-id")
    attachment = conversation.Attachment(
        media_content_id="media-source://media/doorbell.jpg",
        mime_type="image/jpeg",
        path=Path(hass.config.path("doorbell.jpg")),
    )
    chat_log.async_add_user_content(
        conversation.UserContent(content="Describe the door", attachments=[attachment])
    )
    chat_log.llm_api = MagicMock(
        tools=[DummyTool()],
        custom_serializer=None,
    )

    files = [{"type": "input_image", "image_url": "data://img", "detail": "auto"}]

    mock_prepare_files_for_prompt.return_value = files
    messages = _convert_content_to_param(chat_log.content)
    response = await cloud_entity._prepare_chat_for_generation(
        chat_log,
        messages,
        response_format={"type": "json"},
    )

    assert response["conversation_id"] == "conversation-id"
    assert response["response_format"] == {"type": "json"}
    assert response["tool_choice"] == "auto"
    assert len(response["tools"]) == 2
    assert response["tools"][0]["name"] == "do_something"
    assert response["tools"][1]["type"] == "web_search"
    assert response["messages"] is messages
    mock_prepare_files_for_prompt.assert_awaited_once_with([attachment])

    # Verify that files are actually added to the last user message
    last_message = messages[-1]
    assert last_message["type"] == "message"
    assert last_message["role"] == "user"
    assert isinstance(last_message["content"], list)
    assert last_message["content"][0] == {
        "type": "input_text",
        "text": "Describe the door",
    }
    assert last_message["content"][1] == files[0]