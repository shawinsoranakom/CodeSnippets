async def test_execute_block_dry_run_response_format():
    """Dry-run response should look like a normal success (no dry-run signal to LLM)."""
    mock_block = make_mock_block()

    async def fake_simulate(block, input_data, **_kwargs):
        yield "result", "simulated"

    with patch(
        "backend.copilot.tools.helpers.simulate_block", side_effect=fake_simulate
    ):
        response = await execute_block(
            block=mock_block,
            block_id="test-block-id",
            input_data={"query": "hello"},
            user_id="user-1",
            session_id="session-1",
            node_exec_id="node-exec-1",
            matched_credentials={},
            dry_run=True,
        )

    assert isinstance(response, BlockOutputResponse)
    assert "[DRY RUN]" not in response.message
    assert "executed successfully" in response.message
    assert response.success is True
    assert response.outputs == {"result": ["simulated"]}
    # is_dry_run is present in model_dump (used by frontend SSE via StreamToolOutputAvailable).
    # tool_adapter._truncating strips it from the LLM-facing result AFTER stashing,
    # so the frontend receives it but the LLM does not.
    assert response.is_dry_run is True
    assert "is_dry_run" in response.model_dump()
    # model_dump_json excludes None fields — is_dry_run=True must still appear.
    assert '"is_dry_run"' in response.model_dump_json(exclude_none=True)