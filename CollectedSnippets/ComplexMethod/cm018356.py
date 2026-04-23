async def test_generate_image(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_create_stream: AsyncMock,
    entity_registry: er.EntityRegistry,
    issue_registry: ir.IssueRegistry,
    image_model: str,
    input_fidelity_present: bool,
    configured_store: bool,
) -> None:
    """Test AI Task image generation."""
    entity_id = "ai_task.openai_ai_task"

    # Ensure entity is linked to the subentry
    entity_entry = entity_registry.async_get(entity_id)
    ai_task_entry = next(
        iter(
            entry
            for entry in mock_config_entry.subentries.values()
            if entry.subentry_type == "ai_task_data"
        )
    )
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        ai_task_entry,
        data={
            **ai_task_entry.data,
            "image_model": image_model,
            CONF_STORE_RESPONSES: configured_store,
        },
    )
    await hass.async_block_till_done()
    assert entity_entry is not None
    assert entity_entry.config_entry_id == mock_config_entry.entry_id
    assert entity_entry.config_subentry_id == ai_task_entry.subentry_id

    # Mock the OpenAI response stream
    mock_create_stream.return_value = [
        (
            *create_reasoning_item(
                id="rs_A",
                output_index=0,
                reasoning_summary=[["The user asks me to generate an image"]],
            ),
            *create_image_gen_call_item(id="ig_A", output_index=1),
            *create_message_item(id="msg_A", text="", output_index=2),
        )
    ]

    with patch.object(
        media_source.local_source.LocalSource,
        "async_upload_media",
        return_value="media-source://ai_task/image/2025-06-14_225900_test_task.png",
    ) as mock_upload_media:
        result = await ai_task.async_generate_image(
            hass,
            task_name="Test Task",
            entity_id="ai_task.openai_ai_task",
            instructions="Generate test image",
        )

    assert result["height"] == 1024
    assert result["width"] == 1536
    assert result["revised_prompt"] == "Mock revised prompt."
    assert result["mime_type"] == "image/png"
    assert result["model"] == image_model

    mock_upload_media.assert_called_once()
    assert mock_create_stream.call_args is not None
    assert mock_create_stream.call_args.kwargs["store"] is True
    image_tool = next(
        iter(
            tool
            for tool in mock_create_stream.call_args.kwargs["tools"]
            if tool["type"] == "image_generation"
        ),
    )
    assert ("input_fidelity" in image_tool) == input_fidelity_present
    image_data = mock_upload_media.call_args[0][1]
    assert image_data.file.getvalue() == b"A"
    assert image_data.content_type == "image/png"
    assert image_data.filename == "2025-06-14_225900_test_task.png"

    assert (
        issue_registry.async_get_issue(DOMAIN, "organization_verification_required")
        is None
    )