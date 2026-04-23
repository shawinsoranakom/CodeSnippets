def test_get_rate_limit(
    mocker: pytest_mock.MockerFixture,
    configured_snapshot: Snapshot,
    target_user_id: str,
) -> None:
    """Test getting rate limit and usage for a user."""
    _patch_rate_limit_deps(mocker, target_user_id)

    response = client.get("/admin/rate_limit", params={"user_id": target_user_id})

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == target_user_id
    assert data["user_email"] == _TARGET_EMAIL
    assert data["daily_cost_limit_microdollars"] == 2_500_000
    assert data["weekly_cost_limit_microdollars"] == 12_500_000
    assert data["daily_cost_used_microdollars"] == 500_000
    assert data["weekly_cost_used_microdollars"] == 3_000_000
    assert data["tier"] == "FREE"

    configured_snapshot.assert_match(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        "get_rate_limit",
    )