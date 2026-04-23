async def test_generate_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_create_stream: AsyncMock,
    entity_registry: er.EntityRegistry,
    expected_store: bool,
) -> None:
    """Test AI Task data generation."""
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
        data={**ai_task_entry.data, CONF_STORE_RESPONSES: expected_store},
    )
    await hass.async_block_till_done()
    assert entity_entry is not None
    assert entity_entry.config_entry_id == mock_config_entry.entry_id
    assert entity_entry.config_subentry_id == ai_task_entry.subentry_id

    # Mock the OpenAI response stream
    mock_create_stream.return_value = [
        create_message_item(id="msg_A", text="The test data", output_index=0)
    ]

    result = await ai_task.async_generate_data(
        hass,
        task_name="Test Task",
        entity_id=entity_id,
        instructions="Generate test data",
    )

    assert result.data == "The test data"
    assert mock_create_stream.call_args is not None
    assert mock_create_stream.call_args.kwargs["store"] is expected_store