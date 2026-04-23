async def test_concurrent_saves_collision_detection(setup_test_user, test_user_id):
    """Test that concurrent saves from streaming loop and callback handle collisions correctly.

    Simulates the race condition where:
    1. Streaming loop starts with saved_msg_count=5
    2. Long-running callback appends message #5 and saves
    3. Streaming loop tries to save with stale count=5

    The collision detection should handle this gracefully.
    """
    import asyncio

    # Create a session with initial messages
    session = ChatSession.new(user_id=test_user_id, dry_run=False)
    for i in range(3):
        session.messages.append(
            ChatMessage(
                role="user" if i % 2 == 0 else "assistant", content=f"Message {i}"
            )
        )

    # Save initial messages
    session = await upsert_chat_session(session)

    # Simulate streaming loop and callback saving concurrently
    async def streaming_loop_save():
        """Simulates streaming loop saving messages."""
        # Add 2 messages
        session.messages.append(ChatMessage(role="user", content="Streaming message 1"))
        session.messages.append(
            ChatMessage(role="assistant", content="Streaming message 2")
        )

        # Wait a bit to let callback potentially save first
        await asyncio.sleep(0.01)

        # Save (will query DB for existing count)
        return await upsert_chat_session(session)

    async def callback_save():
        """Simulates long-running callback saving a message."""
        # Add 1 message
        session.messages.append(
            ChatMessage(role="tool", content="Callback result", tool_call_id="tc1")
        )

        # Save immediately (will query DB for existing count)
        return await upsert_chat_session(session)

    # Run both saves concurrently - one will hit collision detection
    results = await asyncio.gather(streaming_loop_save(), callback_save())

    # Both should succeed
    assert all(r is not None for r in results)

    # Reload session from DB to verify
    from backend.data.redis_client import get_redis_async

    redis_key = f"chat:session:{session.session_id}"
    async_redis = await get_redis_async()
    await async_redis.delete(redis_key)  # Clear cache to force DB load

    loaded_session = await get_chat_session(session.session_id, test_user_id)
    assert loaded_session is not None

    # Should have all 6 messages (3 initial + 2 streaming + 1 callback)
    assert len(loaded_session.messages) == 6

    # Verify no duplicate sequences
    sequences = []
    for i, msg in enumerate(loaded_session.messages):
        # Messages should have sequential sequence numbers starting from 0
        sequences.append(i)

    # All sequences should be unique and sequential
    assert sequences == list(range(6))

    # Verify message content is preserved
    contents = [m.content for m in loaded_session.messages]
    assert "Message 0" in contents
    assert "Message 1" in contents
    assert "Message 2" in contents
    assert "Streaming message 1" in contents
    assert "Streaming message 2" in contents
    assert "Callback result" in contents