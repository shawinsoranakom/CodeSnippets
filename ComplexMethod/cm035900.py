async def test_search(session_maker):
    store = SaasConversationStore(
        '5594c7b6-f959-4b81-92e9-b09c206f5081',
        UUID('5594c7b6-f959-4b81-92e9-b09c206f5081'),
        session_maker,
    )

    # Create test conversations with different timestamps
    conversations = [
        ConversationMetadata(
            conversation_id=f'conv-{i}',
            user_id='5594c7b6-f959-4b81-92e9-b09c206f5081',
            selected_repository='repo',
            selected_branch=None,
            created_at=datetime(2024, 1, i + 1, tzinfo=UTC),
            last_updated_at=datetime(2024, 1, i + 1, tzinfo=UTC),
        )
        for i in range(5)
    ]

    # Save conversations
    for conv in conversations:
        await store.save_metadata(conv)

    # Test basic search - should return all valid conversations sorted by created_at
    result = await store.search(limit=10)
    assert len(result.results) == 5
    assert [c.conversation_id for c in result.results] == [
        'conv-4',
        'conv-3',
        'conv-2',
        'conv-1',
        'conv-0',
    ]
    assert result.next_page_id is None

    # Test pagination
    result = await store.search(limit=2)
    assert len(result.results) == 2
    assert [c.conversation_id for c in result.results] == ['conv-4', 'conv-3']
    assert result.next_page_id is not None

    # Test next page
    result = await store.search(page_id=result.next_page_id, limit=2)
    assert len(result.results) == 2
    assert [c.conversation_id for c in result.results] == ['conv-2', 'conv-1']