async def test_generate_image(
    hass: HomeAssistant,
    init_components: None,
    mock_ai_task_entity: MockAITaskEntity,
) -> None:
    """Test generating image service."""
    with pytest.raises(
        HomeAssistantError, match="AI Task entity ai_task.unknown not found"
    ):
        await async_generate_image(
            hass,
            task_name="Test Task",
            entity_id="ai_task.unknown",
            instructions="Test prompt",
        )

    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_UNKNOWN

    with patch.object(
        hass.data[DATA_MEDIA_SOURCE],
        "async_upload_media",
        return_value="media-source://ai_task/image/2025-06-14_225900_test_task.png",
    ) as mock_upload_media:
        result = await async_generate_image(
            hass,
            task_name="Test Task",
            entity_id=TEST_ENTITY_ID,
            instructions="Test prompt",
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
    assert result["height"] == 1024
    assert result["width"] == 1536

    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None
    assert state.state != STATE_UNKNOWN

    mock_ai_task_entity.supported_features = AITaskEntityFeature(0)
    with pytest.raises(
        HomeAssistantError,
        match="AI Task entity ai_task.test_task_entity does not support generating images",
    ):
        await async_generate_image(
            hass,
            task_name="Test Task",
            entity_id=TEST_ENTITY_ID,
            instructions="Test prompt",
        )