async def test_auto_top_up_integration(cleanup_test_user, monkeypatch):
    """
    Integration test for auto-top-up functionality that triggers enum casting.

    This tests the complete auto-top-up flow which involves SQL queries with
    CreditTransactionType enums, ensuring enum casting works end-to-end.
    """
    # Enable credits for this test
    from backend.data.credit import settings

    monkeypatch.setattr(settings.config, "enable_credit", True)
    monkeypatch.setattr(settings.config, "enable_beta_monthly_credit", True)
    monkeypatch.setattr(settings.config, "num_user_credits_refill", 1000)

    user_id = cleanup_test_user
    credit_system = BetaUserCredit(1000)

    # First add some initial credits so we can test the configuration and subsequent behavior
    balance, _ = await credit_system._add_transaction(
        user_id=user_id,
        amount=50,  # Below threshold that we'll set
        transaction_type=CreditTransactionType.GRANT,
        metadata=SafeJson({"reason": "Initial credits before auto top-up config"}),
    )
    assert balance == 50

    # Configure auto top-up with threshold above current balance
    config = AutoTopUpConfig(threshold=100, amount=500)
    await set_auto_top_up(user_id, config)

    # Verify configuration was saved but no immediate top-up occurred
    current_balance = await credit_system.get_credits(user_id)
    assert current_balance == 50  # Balance should be unchanged

    # Simulate spending credits that would trigger auto top-up
    # This involves multiple SQL operations with enum casting
    try:
        metadata = UsageTransactionMetadata(reason="Test spend to trigger auto top-up")
        await credit_system.spend_credits(user_id=user_id, cost=10, metadata=metadata)

        # The auto top-up mechanism should have been triggered
        # Verify the transaction types were handled correctly
        transactions = await CreditTransaction.prisma().find_many(
            where={"userId": user_id}, order={"createdAt": "desc"}
        )

        # Should have at least: GRANT (initial), USAGE (spend), and TOP_UP (auto top-up)
        assert len(transactions) >= 3

        # Verify different transaction types exist and enum casting worked
        transaction_types = {t.type for t in transactions}
        assert CreditTransactionType.GRANT in transaction_types
        assert CreditTransactionType.USAGE in transaction_types
        assert (
            CreditTransactionType.TOP_UP in transaction_types
        )  # Auto top-up should have triggered

    except Exception as e:
        # If this fails with enum casting error, the test successfully caught the bug
        if "CreditTransactionType" in str(e) and (
            "cast" in str(e).lower() or "type" in str(e).lower()
        ):
            pytest.fail(f"Enum casting error detected: {e}")
        else:
            # Re-raise other unexpected errors
            raise