def test_get_subscription_status_pro(
    client: fastapi.testclient.TestClient,
    mocker: pytest_mock.MockFixture,
) -> None:
    """GET /credits/subscription returns PRO tier with Stripe price for a PRO user."""
    mock_user = Mock()
    mock_user.subscription_tier = SubscriptionTier.PRO

    async def mock_price_id(tier: SubscriptionTier) -> str | None:
        return "price_pro" if tier == SubscriptionTier.PRO else None

    async def mock_stripe_price_amount(price_id: str) -> int:
        return 1999 if price_id == "price_pro" else 0

    mocker.patch(
        "backend.api.features.v1.get_user_by_id",
        new_callable=AsyncMock,
        return_value=mock_user,
    )
    mocker.patch(
        "backend.api.features.v1.get_subscription_price_id",
        side_effect=mock_price_id,
    )
    mocker.patch(
        "backend.api.features.v1._get_stripe_price_amount",
        side_effect=mock_stripe_price_amount,
    )
    mocker.patch(
        "backend.api.features.v1.get_proration_credit_cents",
        new_callable=AsyncMock,
        return_value=500,
    )

    response = client.get("/credits/subscription")

    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "PRO"
    assert data["monthly_cost"] == 1999
    assert data["tier_costs"]["PRO"] == 1999
    assert data["tier_costs"]["BUSINESS"] == 0
    assert data["tier_costs"]["FREE"] == 0
    assert data["proration_credit_cents"] == 500