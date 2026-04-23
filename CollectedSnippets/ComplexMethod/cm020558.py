async def test_generate_data_service(
    hass: HomeAssistant,
    init_components: None,
    freezer: FrozenDateTimeFactory,
    set_preferences: dict[str, str | None],
    msg_extra: dict[str, str],
    mock_ai_task_entity: MockAITaskEntity,
) -> None:
    """Test the generate data service."""
    preferences = hass.data[DATA_PREFERENCES]
    preferences.async_set_preferences(**set_preferences)

    with patch(
        "homeassistant.components.media_source.async_resolve_media",
        return_value=media_source.PlayMedia(
            url="http://example.com/media.mp4",
            mime_type="video/mp4",
            path=Path("media.mp4"),
        ),
    ):
        result = await hass.services.async_call(
            "ai_task",
            "generate_data",
            {
                "task_name": "Test Name",
                "instructions": "Test prompt",
            }
            | msg_extra,
            blocking=True,
            return_response=True,
        )

    assert result["data"] == "Mock result"

    assert len(mock_ai_task_entity.mock_generate_data_tasks) == 1
    task = mock_ai_task_entity.mock_generate_data_tasks[0]

    assert len(task.attachments or []) == len(
        msg_attachments := msg_extra.get("attachments", [])
    )

    for msg_attachment, attachment in zip(
        msg_attachments, task.attachments or [], strict=False
    ):
        assert attachment.mime_type == "video/mp4"
        assert attachment.media_content_id == msg_attachment["media_content_id"]
        assert attachment.path == Path("media.mp4")