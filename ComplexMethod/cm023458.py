async def test_generate_image(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_generate_content: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test AI Task image generation."""
    mock_image_data = b"fake_image_data"
    mock_generate_content.return_value = Mock(
        text="Here is your generated image",
        prompt_feedback=None,
        candidates=[
            Mock(
                content=Mock(
                    parts=[
                        Mock(
                            text="Here is your generated image",
                            inline_data=None,
                            thought=False,
                        ),
                        Mock(
                            inline_data=Mock(
                                data=mock_image_data, mime_type="image/png"
                            ),
                            text=None,
                            thought=False,
                        ),
                    ]
                )
            )
        ],
    )

    with patch.object(
        media_source.local_source.LocalSource,
        "async_upload_media",
        return_value="media-source://ai_task/image/2025-06-14_225900_test_task.png",
    ) as mock_upload_media:
        result = await ai_task.async_generate_image(
            hass,
            task_name="Test Task",
            entity_id="ai_task.google_ai_task",
            instructions="Generate a test image",
        )

    assert result["height"] is None
    assert result["width"] is None
    assert result["revised_prompt"] == "Generate a test image"
    assert result["mime_type"] == "image/png"
    assert result["model"] == RECOMMENDED_IMAGE_MODEL.partition("/")[-1]

    mock_upload_media.assert_called_once()
    image_data = mock_upload_media.call_args[0][1]
    assert image_data.file.getvalue() == mock_image_data
    assert image_data.content_type == "image/png"
    assert image_data.filename == "2025-06-14_225900_test_task.png"

    # Verify that generate_content was called with correct parameters
    assert mock_generate_content.called
    call_args = mock_generate_content.call_args
    assert call_args.kwargs["model"] == RECOMMENDED_IMAGE_MODEL
    assert call_args.kwargs["contents"] == ["Generate a test image"]
    assert call_args.kwargs["config"].response_modalities == ["TEXT", "IMAGE"]