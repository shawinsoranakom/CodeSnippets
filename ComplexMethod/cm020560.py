async def test_generate_image_service(
    hass: HomeAssistant,
    init_components: None,
    set_preferences: dict[str, str | None],
    msg_extra: dict[str, str],
    mock_ai_task_entity: MockAITaskEntity,
) -> None:
    """Test the generate image service."""
    preferences = hass.data[DATA_PREFERENCES]
    preferences.async_set_preferences(**set_preferences)

    with patch.object(
        hass.data[DATA_MEDIA_SOURCE],
        "async_upload_media",
        return_value="media-source://ai_task/image/2025-06-14_225900_test_task.png",
    ) as mock_upload_media:
        result = await hass.services.async_call(
            "ai_task",
            "generate_image",
            {
                "task_name": "Test Image",
                "instructions": "Generate a test image",
            }
            | msg_extra,
            blocking=True,
            return_response=True,
        )

    mock_upload_media.assert_called_once()
    assert "image_data" not in result
    assert (
        result["media_source_id"]
        == "media-source://ai_task/image/2025-06-14_225900_test_task.png"
    )
    assert result["url"].startswith(
        "/ai_task/image/2025-06-14_225900_test_task.png?authSig="
    )
    assert result["mime_type"] == "image/png"
    assert result["model"] == "mock_model"
    assert result["revised_prompt"] == "mock_revised_prompt"

    assert len(mock_ai_task_entity.mock_generate_image_tasks) == 1
    task = mock_ai_task_entity.mock_generate_image_tasks[0]
    assert task.instructions == "Generate a test image"