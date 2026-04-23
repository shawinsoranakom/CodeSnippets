async def test_session_metadata_json_serialization():
    """Test that session_metadata is properly serialized as JSON."""
    session_id = f"json_test_session_{uuid4()}"
    metadata = {
        "tenant_id": "tenant-json",
        "nested": {"key1": "value1", "key2": [1, 2, 3]},
        "array": ["item1", "item2"],
        "number": 42,
        "boolean": True,
    }

    message = Message(
        text="JSON serialization test",
        sender="User",
        sender_name="Test User",
        session_id=session_id,
        session_metadata=metadata,
    )
    await astore_message(message)

    # Retrieve and verify complex JSON structure
    retrieved_messages = await aget_messages(sender="User", session_id=session_id)
    assert len(retrieved_messages) == 1
    retrieved_metadata = retrieved_messages[0].session_metadata

    assert retrieved_metadata["tenant_id"] == "tenant-json"
    assert retrieved_metadata["nested"]["key1"] == "value1"
    assert retrieved_metadata["nested"]["key2"] == [1, 2, 3]
    assert retrieved_metadata["array"] == ["item1", "item2"]
    assert retrieved_metadata["number"] == 42
    assert retrieved_metadata["boolean"] is True