async def test_metadata_json_serialization(setup_test_user):
    """Test that metadata is properly serialized for JSONB column in raw SQL."""
    user_id = setup_test_user
    credit_system = BetaUserCredit(1000)

    # Test with complex metadata that would fail if not properly serialized
    complex_metadata = SafeJson(
        {
            "graph_exec_id": "test-12345",
            "reason": "Testing metadata serialization",
            "nested_data": {
                "key1": "value1",
                "key2": ["array", "of", "values"],
                "key3": {"deeply": {"nested": "object"}},
            },
            "special_chars": "Testing 'quotes' and \"double quotes\" and unicode: 🚀",
        }
    )

    # This should work without throwing a JSONB casting error
    balance, tx_key = await credit_system._add_transaction(
        user_id=user_id,
        amount=500,  # $5 top-up
        transaction_type=CreditTransactionType.TOP_UP,
        metadata=complex_metadata,
        is_active=True,
    )

    # Verify the transaction was created successfully
    assert balance == 500

    # Verify the metadata was stored correctly in the database
    transaction = await CreditTransaction.prisma().find_first(
        where={"userId": user_id, "transactionKey": tx_key}
    )

    assert transaction is not None
    assert transaction.metadata is not None

    # Verify the metadata contains our complex data
    metadata_dict: dict[str, Any] = dict(transaction.metadata)  # type: ignore
    assert metadata_dict["graph_exec_id"] == "test-12345"
    assert metadata_dict["reason"] == "Testing metadata serialization"
    assert metadata_dict["nested_data"]["key1"] == "value1"
    assert metadata_dict["nested_data"]["key3"]["deeply"]["nested"] == "object"
    assert (
        metadata_dict["special_chars"]
        == "Testing 'quotes' and \"double quotes\" and unicode: 🚀"
    )