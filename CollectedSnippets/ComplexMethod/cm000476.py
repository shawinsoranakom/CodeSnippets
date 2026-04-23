async def test_modify_stripe_subscription_for_tier_downgrade_creates_schedule():
    """Paid→paid downgrade (BUSINESS→PRO) creates a Subscription Schedule rather than proration."""
    import time as time_mod

    now = int(time_mod.time())
    period_end = now + 27 * 24 * 3600
    mock_sub = stripe.Subscription.construct_from(
        {
            "id": "sub_biz",
            "items": {"data": [{"id": "si_biz", "price": {"id": "price_biz_monthly"}}]},
            "current_period_start": now - 3 * 24 * 3600,
            "current_period_end": period_end,
            "schedule": None,
            "cancel_at_period_end": False,
        },
        "k",
    )
    mock_list = MagicMock()
    mock_list.data = [mock_sub]

    mock_user = MagicMock(spec=User)
    mock_user.stripe_customer_id = "cus_abc"
    mock_user.subscription_tier = SubscriptionTier.BUSINESS

    mock_schedule = stripe.SubscriptionSchedule.construct_from(
        {"id": "sub_sched_1"}, "k"
    )

    with (
        patch(
            "backend.data.credit.get_subscription_price_id",
            new_callable=AsyncMock,
            return_value="price_pro_monthly",
        ),
        patch(
            "backend.data.credit.get_user_by_id",
            new_callable=AsyncMock,
            return_value=mock_user,
        ),
        patch(
            "backend.data.credit.stripe.Subscription.list_async",
            new_callable=AsyncMock,
            return_value=mock_list,
        ),
        patch(
            "backend.data.credit.stripe.Subscription.modify_async",
            new_callable=AsyncMock,
        ) as mock_modify,
        patch(
            "backend.data.credit.stripe.SubscriptionSchedule.create_async",
            new_callable=AsyncMock,
            return_value=mock_schedule,
        ) as mock_schedule_create,
        patch(
            "backend.data.credit.stripe.SubscriptionSchedule.modify_async",
            new_callable=AsyncMock,
        ) as mock_schedule_modify,
    ):
        result = await modify_stripe_subscription_for_tier(
            "user-1", SubscriptionTier.PRO
        )

    assert result is True
    # Did NOT call Subscription.modify with proration (no immediate tier change).
    mock_modify.assert_not_called()
    mock_schedule_create.assert_called_once_with(from_subscription="sub_biz")
    assert mock_schedule_modify.call_count == 1
    _, kwargs = mock_schedule_modify.call_args
    phases = kwargs["phases"]
    assert phases[0]["items"][0]["price"] == "price_biz_monthly"
    assert phases[0]["end_date"] == period_end
    assert phases[1]["items"][0]["price"] == "price_pro_monthly"
    assert phases[0]["proration_behavior"] == "none"
    assert phases[1]["proration_behavior"] == "none"