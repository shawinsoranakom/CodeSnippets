def test_usage_returns_daily_and_weekly(
    mocker: pytest_mock.MockerFixture,
    test_user_id: str,
) -> None:
    """GET /usage returns percentages for daily and weekly windows only.

    The raw used/limit microdollar values MUST NOT leak — clients should not
    be able to derive per-turn cost or platform margins from the public API.
    """
    mock_get = _mock_usage(mocker, daily_used=500, weekly_used=2000)

    mocker.patch.object(chat_routes.config, "daily_cost_limit_microdollars", 10000)
    mocker.patch.object(chat_routes.config, "weekly_cost_limit_microdollars", 50000)

    response = client.get("/usage")

    assert response.status_code == 200
    data = response.json()
    # 500 / 10000 = 5%, 2000 / 50000 = 4%
    assert data["daily"]["percent_used"] == 5.0
    assert data["weekly"]["percent_used"] == 4.0
    # Raw spend/limit must not be exposed.
    assert "used" not in data["daily"]
    assert "limit" not in data["daily"]
    assert "used" not in data["weekly"]
    assert "limit" not in data["weekly"]

    mock_get.assert_called_once_with(
        user_id=test_user_id,
        daily_cost_limit=10000,
        weekly_cost_limit=50000,
        rate_limit_reset_cost=chat_routes.config.rate_limit_reset_cost,
        tier=SubscriptionTier.FREE,
    )