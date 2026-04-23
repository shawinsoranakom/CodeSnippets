def test_transaction_excludes_code_key(session):
    """Test that the code key is excluded from transaction inputs when logged to the database."""
    from langflow.services.database.models.transactions.model import TransactionTable

    # Create a flow to associate with the transaction
    flow = Flow(name=str(uuid4()), description="Test flow", data={})
    session.add(flow)
    session.commit()
    session.refresh(flow)

    # Create input data with a code key
    input_data = {"param1": "value1", "param2": "value2", "code": "print('Hello, world!')"}

    # Create a transaction with inputs containing a code key
    transaction = TransactionTable(
        timestamp=datetime.now(timezone.utc),
        vertex_id="test-vertex",
        target_id="test-target",
        inputs=input_data,
        outputs={"result": "success"},
        status="completed",
        flow_id=flow.id,
    )

    # Verify that the code key is removed during transaction creation
    assert transaction.inputs is not None
    assert "code" not in transaction.inputs
    assert "param1" in transaction.inputs
    assert "param2" in transaction.inputs

    # Add the transaction to the database
    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    # Verify that the code key is not in the saved transaction inputs
    assert transaction.inputs is not None
    assert "code" not in transaction.inputs
    assert "param1" in transaction.inputs
    assert "param2" in transaction.inputs