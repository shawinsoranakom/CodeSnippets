async def test_full_tag_roundtrip_with_automation_context(async_session, service):
    """Full integration test: save tags, load, verify, update, verify again."""
    conversation_id = uuid4()

    # Initial save with automation tags
    initial_tags = {
        'trigger': 'webhook',
        'automation_id': 'auto-abc',
        'automation_name': 'Daily Report',
        'run_id': 'run-xyz',
        'plugins': 'https://github.com/OpenHands/skill1,https://github.com/OpenHands/skill2',
    }

    stored = StoredConversationMetadata(
        conversation_id=str(conversation_id),
        sandbox_id='sandbox_123',
        title='Automation Conversation',
        tags=initial_tags,
        trigger='automation',
        conversation_version='V1',
        pr_number=[],
        created_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
    )
    async_session.add(stored)
    await async_session.commit()

    # Load and verify
    result = await service.get_app_conversation_info(conversation_id)
    assert result is not None
    assert result.tags == initial_tags
    assert result.tags['trigger'] == 'webhook'
    assert result.tags['automation_id'] == 'auto-abc'
    assert 'skill1' in result.tags['plugins']
    assert 'skill2' in result.tags['plugins']

    # Update with additional tag
    result.tags['custom_key'] = 'custom_value'
    stored.tags = result.tags
    await async_session.commit()

    # Reload and verify update
    result2 = await service.get_app_conversation_info(conversation_id)
    assert result2.tags['custom_key'] == 'custom_value'
    # Original tags should still be present
    assert result2.tags['automation_id'] == 'auto-abc'