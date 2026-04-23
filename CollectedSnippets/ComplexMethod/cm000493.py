async def test_enable_transaction_enum_casting_integration(cleanup_test_user):
    """
    Integration test for _enable_transaction with enum casting.

    Tests the scenario where inactive transactions are enabled, which also
    involves SQL queries with CreditTransactionType enum casting.
    """
    user_id = cleanup_test_user
    credit_system = BetaUserCredit(1000)

    # Create an inactive transaction
    balance, tx_key = await credit_system._add_transaction(
        user_id=user_id,
        amount=100,
        transaction_type=CreditTransactionType.TOP_UP,
        metadata=SafeJson({"reason": "Inactive transaction test"}),
        is_active=False,  # Create as inactive
    )

    # Balance should be 0 since transaction is inactive
    assert balance == 0

    # Enable the transaction with new metadata
    enable_metadata = SafeJson(
        {
            "payment_method": "test_payment",
            "activation_reason": "Integration test activation",
        }
    )

    # This would fail with enum casting error before the fix
    final_balance = await credit_system._enable_transaction(
        transaction_key=tx_key,
        user_id=user_id,
        metadata=enable_metadata,
    )

    # Now balance should reflect the activated transaction
    assert final_balance == 100

    # Verify transaction was properly enabled with correct enum type
    transaction = await CreditTransaction.prisma().find_first(
        where={"userId": user_id, "transactionKey": tx_key}
    )

    assert transaction is not None
    assert transaction.isActive is True
    assert transaction.type == CreditTransactionType.TOP_UP
    assert transaction.runningBalance == 100

    # Verify metadata was updated
    assert transaction.metadata is not None
    assert transaction.metadata["payment_method"] == "test_payment"
    assert transaction.metadata["activation_reason"] == "Integration test activation"