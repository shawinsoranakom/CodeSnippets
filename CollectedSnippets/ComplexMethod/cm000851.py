async def test_logs_cost_entry_with_cost_usd(self):
        """When cost_usd is provided, tracking_type should be 'cost_usd'."""
        mock_log = AsyncMock()
        with (
            patch(
                "backend.copilot.token_tracking.record_cost_usage",
                new_callable=AsyncMock,
            ),
            patch(
                "backend.copilot.token_tracking.platform_cost_db",
                return_value=type(
                    "FakePlatformCostDb", (), {"log_platform_cost": mock_log}
                )(),
            ),
        ):
            await persist_and_record_usage(
                session=_make_session(),
                user_id="user-cost",
                prompt_tokens=200,
                completion_tokens=100,
                cost_usd=0.005,
                model="gpt-4",
                provider="anthropic",
                log_prefix="[SDK]",
            )
            await asyncio.sleep(0)
        mock_log.assert_awaited_once()
        entry = mock_log.call_args[0][0]
        assert entry.user_id == "user-cost"
        assert entry.provider == "anthropic"
        assert entry.model == "gpt-4"
        assert entry.cost_microdollars == 5000
        assert entry.input_tokens == 200
        assert entry.output_tokens == 100
        assert entry.tracking_type == "cost_usd"
        assert entry.metadata["tracking_type"] == "cost_usd"
        assert entry.metadata["tracking_amount"] == 0.005
        assert entry.block_name == "copilot:SDK"
        assert entry.graph_exec_id == "sess-test"