async def test_session_metadata_persistence_and_retrieval(sample_session_metadata):
    """Test full cycle: create, store, retrieve, and verify session_metadata."""
    session_id = f"full_cycle_session_{uuid4()}"

    # Create and store
    message = Message(
        text="Full cycle test message",
        sender="User",
        sender_name="Test User",
        session_id=session_id,
        session_metadata=sample_session_metadata,
    )
    await astore_message(message)

    # Retrieve
    retrieved_messages = await aget_messages(sender="User", session_id=session_id)

    # Verify
    assert len(retrieved_messages) == 1
    retrieved = retrieved_messages[0]
    assert retrieved.text == "Full cycle test message"
    assert retrieved.session_metadata is not None
    assert retrieved.session_metadata["tenant_id"] == "tenant-123"
    assert retrieved.session_metadata["user_id"] == "user-456"
    assert retrieved.session_metadata["region"] == "us-east-1"
    assert retrieved.session_metadata["retention_profile"] == "standard"
    assert retrieved.session_metadata["data_flags"]["pii"] is True
    assert retrieved.session_metadata["custom_fields"]["department"] == "engineering"