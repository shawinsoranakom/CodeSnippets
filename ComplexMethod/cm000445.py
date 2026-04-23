async def test_returns_dashboard_with_data(self):
        provider_row = _make_group_by_row(
            provider="openai",
            tracking_type="tokens",
            cost=5000,
            input_tokens=1000,
            output_tokens=500,
            duration=10.5,
            count=3,
        )
        user_row = _make_group_by_row(user_id="u1", cost=5000, count=3)

        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.email = "a@b.com"

        mock_actions = MagicMock()
        mock_actions.group_by = AsyncMock(
            side_effect=[
                [provider_row],  # by_provider
                [user_row],  # by_user
                [],  # by_user_tracking_groups (no cost_usd rows for this user)
                [{"userId": "u1"}],  # distinct users
                [provider_row],  # total agg (tracking_type=None → same as unfiltered)
            ]
        )
        mock_actions.find_many = AsyncMock(return_value=[mock_user])

        with (
            patch(
                "backend.data.platform_cost.PrismaLog.prisma",
                return_value=mock_actions,
            ),
            patch(
                "backend.data.platform_cost.PrismaUser.prisma",
                return_value=mock_actions,
            ),
            patch(
                "backend.data.platform_cost.query_raw_with_schema",
                new_callable=AsyncMock,
                side_effect=[
                    [{"p50": 1000, "p75": 2000, "p95": 4000, "p99": 5000}],
                    [{"bucket": "$0-0.50", "count": 3}],
                ],
            ),
        ):
            dashboard = await get_platform_cost_dashboard()

        assert dashboard.total_cost_microdollars == 5000
        assert dashboard.total_requests == 3
        assert dashboard.total_users == 1
        assert len(dashboard.by_provider) == 1
        assert dashboard.by_provider[0].provider == "openai"
        assert dashboard.by_provider[0].tracking_type == "tokens"
        assert dashboard.by_provider[0].total_duration_seconds == 10.5
        assert len(dashboard.by_user) == 1
        assert dashboard.by_user[0].email == "a***@b.com"
        assert dashboard.cost_p50_microdollars == 1000
        assert dashboard.cost_p75_microdollars == 2000
        assert dashboard.cost_p95_microdollars == 4000
        assert dashboard.cost_p99_microdollars == 5000
        assert len(dashboard.cost_buckets) == 1
        # total_input/output_tokens come from total_agg_no_tracking_type_groups
        # (provider_row has 1000/500)
        assert dashboard.total_input_tokens == 1000
        assert dashboard.total_output_tokens == 500
        # Token averages must use token_bearing_requests (3) not cost_bearing (0)
        assert dashboard.avg_input_tokens_per_request == pytest.approx(1000 / 3)
        assert dashboard.avg_output_tokens_per_request == pytest.approx(500 / 3)
        # No cost_usd rows in total_agg → avg_cost should be 0
        assert dashboard.avg_cost_microdollars_per_request == 0.0