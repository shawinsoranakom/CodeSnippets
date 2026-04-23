async def test_returns_empty_dashboard(self):
        mock_actions = MagicMock()
        mock_actions.group_by = AsyncMock(side_effect=[[], [], [], [], []])
        mock_actions.find_many = AsyncMock(return_value=[])

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
                side_effect=[[], []],
            ),
        ):
            dashboard = await get_platform_cost_dashboard()

        assert dashboard.total_cost_microdollars == 0
        assert dashboard.total_requests == 0
        assert dashboard.total_users == 0
        assert dashboard.by_provider == []
        assert dashboard.by_user == []
        assert dashboard.cost_p50_microdollars == 0
        assert dashboard.cost_buckets == []