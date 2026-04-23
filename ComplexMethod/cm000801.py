async def test_chatsession_db_storage(setup_test_user, test_user_id):
    """Test that messages are correctly saved to and loaded from DB (not cache)."""
    from backend.data.redis_client import get_redis_async

    # Create session with messages including assistant message
    s = ChatSession.new(user_id=test_user_id, dry_run=False)
    s.messages = messages  # Contains user, assistant, and tool messages
    assert s.session_id is not None, "Session id is not set"
    # Upsert to save to both cache and DB
    s = await upsert_chat_session(s)

    # Clear the Redis cache to force DB load
    redis_key = f"chat:session:{s.session_id}"
    async_redis = await get_redis_async()
    await async_redis.delete(redis_key)

    # Load from DB (cache was cleared)
    s2 = await get_chat_session(
        session_id=s.session_id,
        user_id=s.user_id,
    )

    assert s2 is not None, "Session not found after loading from DB"
    assert len(s2.messages) == len(
        s.messages
    ), f"Message count mismatch: expected {len(s.messages)}, got {len(s2.messages)}"

    # Verify all roles are present
    roles = [m.role for m in s2.messages]
    assert "user" in roles, f"User message missing. Roles found: {roles}"
    assert "assistant" in roles, f"Assistant message missing. Roles found: {roles}"
    assert "tool" in roles, f"Tool message missing. Roles found: {roles}"

    # Verify message content
    for orig, loaded in zip(s.messages, s2.messages):
        assert orig.role == loaded.role, f"Role mismatch: {orig.role} != {loaded.role}"
        assert (
            orig.content == loaded.content
        ), f"Content mismatch for {orig.role}: {orig.content} != {loaded.content}"
        if orig.tool_calls:
            assert (
                loaded.tool_calls is not None
            ), f"Tool calls missing for {orig.role} message"
            assert len(orig.tool_calls) == len(loaded.tool_calls)