async def test_credit_transaction_enum_casting_integration(cleanup_test_user):
    """
    Integration test to verify CreditTransactionType enum casting works in SQL queries.

    This test would have caught the enum casting bug where PostgreSQL expected
    platform."CreditTransactionType" but got "CreditTransactionType".
    """
    user_id = cleanup_test_user
    credit_system = BetaUserCredit(1000)

    # Test each transaction type to ensure enum casting works
    test_cases = [
        (CreditTransactionType.TOP_UP, 100, "Test top-up"),
        (CreditTransactionType.USAGE, -50, "Test usage"),
        (CreditTransactionType.GRANT, 200, "Test grant"),
        (CreditTransactionType.REFUND, -25, "Test refund"),
        (CreditTransactionType.CARD_CHECK, 0, "Test card check"),
    ]

    for transaction_type, amount, reason in test_cases:
        metadata = SafeJson({"reason": reason, "test": "enum_casting"})

        # This call would fail with enum casting error before the fix
        balance, tx_key = await credit_system._add_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            metadata=metadata,
            is_active=True,
        )

        # Verify transaction was created with correct type
        transaction = await CreditTransaction.prisma().find_first(
            where={"userId": user_id, "transactionKey": tx_key}
        )

        assert transaction is not None
        assert transaction.type == transaction_type
        assert transaction.amount == amount
        assert transaction.metadata is not None

        # Verify metadata content
        assert transaction.metadata["reason"] == reason
        assert transaction.metadata["test"] == "enum_casting"