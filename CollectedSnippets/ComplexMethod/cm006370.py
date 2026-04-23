async def test_code_key_not_saved_to_database():
    """Test that the code key is not saved to the database."""
    # Create input data with a code key
    input_data = {"param1": "value1", "param2": "value2", "code": "print('Hello, world!')"}

    # Create a transaction with inputs containing a code key
    transaction = TransactionBase(
        timestamp=datetime.now(timezone.utc),
        vertex_id="test-vertex",
        target_id="test-target",
        inputs=input_data,
        outputs={"result": "success"},
        status="completed",
        flow_id=uuid.uuid4(),
    )

    # Verify that the code key is removed during transaction creation
    assert transaction.inputs is not None
    assert "code" not in transaction.inputs
    assert "param1" in transaction.inputs
    assert "param2" in transaction.inputs

    # Verify that the code key is excluded when serializing
    serialized_inputs = transaction.serialize_inputs(transaction.inputs)
    assert "code" not in serialized_inputs
    assert "param1" in serialized_inputs
    assert "param2" in serialized_inputs