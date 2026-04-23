async def test_search_pagination():
    # Create test data with 5 conversations
    store = FileConversationStore(
        InMemoryFileStore(
            {
                get_conversation_metadata_filename(f'conv{i}'): json.dumps(
                    {
                        'conversation_id': f'conv{i}',
                        'user_id': '123',
                        'selected_repository': 'repo1',
                        'title': f'ServerConversation {i}',
                        'created_at': f'2025-01-{15 + i}T19:51:04Z',
                    }
                )
                for i in range(1, 6)
            }
        )
    )

    # Test with limit of 2
    result = await store.search(limit=2)
    assert len(result.results) == 2
    assert result.results[0].conversation_id == 'conv5'  # newest first
    assert result.results[1].conversation_id == 'conv4'
    assert result.next_page_id is not None

    # Get next page using the next_page_id
    result2 = await store.search(page_id=result.next_page_id, limit=2)
    assert len(result2.results) == 2
    assert result2.results[0].conversation_id == 'conv3'
    assert result2.results[1].conversation_id == 'conv2'
    assert result2.next_page_id is not None

    # Get last page
    result3 = await store.search(page_id=result2.next_page_id, limit=2)
    assert len(result3.results) == 1
    assert result3.results[0].conversation_id == 'conv1'
    assert result3.next_page_id is None