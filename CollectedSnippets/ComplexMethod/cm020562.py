async def test_generate_data_mixed_attachments(
    hass: HomeAssistant,
    init_components: None,
    mock_ai_task_entity: MockAITaskEntity,
) -> None:
    """Test generating data with both camera and regular media source attachments."""
    with (
        patch(
            "homeassistant.components.camera.async_get_image",
            return_value=Image(content_type="image/jpeg", content=b"fake_camera_jpeg"),
        ) as mock_get_camera_image,
        patch(
            "homeassistant.components.image.async_get_image",
            return_value=Image(content_type="image/jpeg", content=b"fake_image_jpeg"),
        ) as mock_get_image_image,
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            return_value=media_source.PlayMedia(
                url="http://example.com/test.mp4",
                mime_type="video/mp4",
                path=Path("/media/test.mp4"),
            ),
        ) as mock_resolve_media,
    ):
        await async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=TEST_ENTITY_ID,
            instructions="Analyze these files",
            attachments=[
                {
                    "media_content_id": "media-source://camera/camera.front_door",
                    "media_content_type": "image/jpeg",
                },
                {
                    "media_content_id": "media-source://image/image.floorplan",
                    "media_content_type": "image/jpeg",
                },
                {
                    "media_content_id": "media-source://media_player/video.mp4",
                    "media_content_type": "video/mp4",
                },
            ],
        )

    # Verify both methods were called
    mock_get_camera_image.assert_called_once_with(hass, "camera.front_door")
    mock_get_image_image.assert_called_once_with(hass, "image.floorplan")
    mock_resolve_media.assert_called_once_with(
        hass, "media-source://media_player/video.mp4", None
    )

    # Check attachments
    assert len(mock_ai_task_entity.mock_generate_data_tasks) == 1
    task = mock_ai_task_entity.mock_generate_data_tasks[0]
    assert task.attachments is not None
    assert len(task.attachments) == 3

    # Check camera attachment
    camera_attachment = task.attachments[0]
    assert (
        camera_attachment.media_content_id == "media-source://camera/camera.front_door"
    )
    assert camera_attachment.mime_type == "image/jpeg"
    assert isinstance(camera_attachment.path, Path)
    assert camera_attachment.path.suffix == ".jpg"

    # Verify camera snapshot content
    assert camera_attachment.path.exists()
    content = await hass.async_add_executor_job(camera_attachment.path.read_bytes)
    assert content == b"fake_camera_jpeg"

    # Check image attachment
    image_attachment = task.attachments[1]
    assert image_attachment.media_content_id == "media-source://image/image.floorplan"
    assert image_attachment.mime_type == "image/jpeg"
    assert isinstance(image_attachment.path, Path)
    assert image_attachment.path.suffix == ".jpg"

    # Verify image snapshot content
    assert image_attachment.path.exists()
    content = await hass.async_add_executor_job(image_attachment.path.read_bytes)
    assert content == b"fake_image_jpeg"

    # Trigger clean up
    async_fire_time_changed(
        hass,
        dt_util.utcnow() + chat_session.CONVERSATION_TIMEOUT + timedelta(seconds=1),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    # Verify the temporary file cleaned up
    assert not camera_attachment.path.exists()
    assert not image_attachment.path.exists()

    # Check regular media attachment
    media_attachment = task.attachments[2]
    assert media_attachment.media_content_id == "media-source://media_player/video.mp4"
    assert media_attachment.mime_type == "video/mp4"
    assert media_attachment.path == Path("/media/test.mp4")