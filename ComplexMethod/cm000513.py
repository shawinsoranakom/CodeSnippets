async def test_enable_transaction_metadata_serialization(setup_test_user):
    """Test that _enable_transaction also handles metadata JSON serialization correctly."""
    user_id = setup_test_user
    credit_system = BetaUserCredit(1000)

    # First create an inactive transaction
    balance, tx_key = await credit_system._add_transaction(
        user_id=user_id,
        amount=300,
        transaction_type=CreditTransactionType.TOP_UP,
        metadata=SafeJson({"initial": "inactive_transaction"}),
        is_active=False,  # Create as inactive
    )

    # Initial balance should be 0 because transaction is inactive
    assert balance == 0

    # Now enable the transaction with new metadata
    enable_metadata = SafeJson(
        {
            "payment_method": "stripe",
            "payment_intent": "pi_test_12345",
            "activation_reason": "Payment confirmed",
            "complex_data": {"array": [1, 2, 3], "boolean": True, "null_value": None},
        }
    )

    # This should work without JSONB casting errors
    final_balance = await credit_system._enable_transaction(
        transaction_key=tx_key,
        user_id=user_id,
        metadata=enable_metadata,
    )

    # Now balance should reflect the activated transaction
    assert final_balance == 300

    # Verify the metadata was updated correctly
    transaction = await CreditTransaction.prisma().find_first(
        where={"userId": user_id, "transactionKey": tx_key}
    )

    assert transaction is not None
    assert transaction.isActive is True

    # Verify the metadata was updated with enable_metadata
    metadata_dict: dict[str, Any] = dict(transaction.metadata)  # type: ignore
    assert metadata_dict["payment_method"] == "stripe"
    assert metadata_dict["payment_intent"] == "pi_test_12345"
    assert metadata_dict["complex_data"]["array"] == [1, 2, 3]
    assert metadata_dict["complex_data"]["boolean"] is True
    assert metadata_dict["complex_data"]["null_value"] is None