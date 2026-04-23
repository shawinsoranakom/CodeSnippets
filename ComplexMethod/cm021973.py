async def test_generate_data_with_attachments(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    mock_create_stream: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test AI Task data generation with attachments."""
    entity_id = "ai_task.claude_ai_task"

    mock_create_stream.return_value = [create_content_block(0, ["Hi there!"])]

    # Test with attachments
    with (
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            side_effect=[
                media_source.PlayMedia(
                    url="http://example.com/doorbell_snapshot.jpg",
                    mime_type="image/jpg",
                    path=Path("doorbell_snapshot.jpg"),
                ),
                media_source.PlayMedia(
                    url="http://example.com/context.pdf",
                    mime_type="application/pdf",
                    path=Path("context.pdf"),
                ),
            ],
        ),
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_bytes", return_value=b"fake_image_data"),
    ):
        result = await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=entity_id,
            instructions="Test prompt",
            attachments=[
                {"media_content_id": "media-source://media/doorbell_snapshot.jpg"},
                {"media_content_id": "media-source://media/context.pdf"},
            ],
        )

    assert result.data == "Hi there!"

    # Verify that the create stream was called with the correct parameters
    # The last call should have the user message with attachments
    call_args = mock_create_stream.call_args
    assert call_args is not None

    # Check that the input includes the attachments
    input_messages = call_args[1]["messages"]
    assert len(input_messages) > 0

    # Find the user message with attachments
    user_message_with_attachments = input_messages[-2]

    assert user_message_with_attachments is not None
    assert isinstance(user_message_with_attachments["content"], list)
    assert len(user_message_with_attachments["content"]) == 3  # Text + attachments

    text_block, image_block, document_block = user_message_with_attachments["content"]

    # Text block
    assert text_block["type"] == "text"
    assert text_block["text"] == "Test prompt"

    # Image attachment
    assert image_block["type"] == "image"
    assert image_block["source"] == {
        "data": "ZmFrZV9pbWFnZV9kYXRh",
        "media_type": "image/jpeg",
        "type": "base64",
    }

    # Document attachment (ignore extra metadata like cache_control)
    assert document_block["type"] == "document"
    assert document_block["source"]["data"] == "ZmFrZV9pbWFnZV9kYXRh"
    assert document_block["source"]["media_type"] == "application/pdf"
    assert document_block["source"]["type"] == "base64"