async def test_logs_with_system_credential(self):
        db_client = _make_db_client()
        with (
            patch(
                "backend.executor.cost_tracking.is_system_credential", return_value=True
            ),
            patch(
                "backend.executor.cost_tracking.block_usage_cost",
                return_value=(10, None),
            ),
        ):
            node_exec = _make_node_exec(
                inputs={
                    "credentials": {"id": "sys-cred-1", "provider": "openai"},
                    "model": "gpt-4",
                }
            )
            block = _make_block()
            stats = NodeExecutionStats(input_token_count=500, output_token_count=200)
            await log_system_credential_cost(node_exec, block, stats, db_client)
            await asyncio.sleep(0)

        db_client.log_platform_cost.assert_awaited_once()
        entry = db_client.log_platform_cost.call_args[0][0]
        assert entry.user_id == "user-1"
        assert entry.provider == "openai"
        assert entry.block_name == "TestBlock"
        assert entry.model == "gpt-4"
        assert entry.input_tokens == 500
        assert entry.output_tokens == 200
        assert entry.tracking_type == "tokens"
        assert entry.metadata["tracking_type"] == "tokens"
        assert entry.metadata["tracking_amount"] == 700.0
        assert entry.metadata["credit_cost"] == 10