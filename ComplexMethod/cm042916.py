async def test_state_export_includes_stack_and_dfs_seen(self):
        """Verify DFS state includes stack structure and _dfs_seen."""
        captured_states: List[Dict] = []

        async def capture_state(state: Dict[str, Any]):
            captured_states.append(state)

        strategy = DFSDeepCrawlStrategy(
            max_depth=3,
            max_pages=10,
            on_state_change=capture_state,
        )

        mock_crawler = create_mock_crawler_with_links(num_links=2)
        mock_config = create_mock_config()

        await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        assert len(captured_states) > 0

        for state in captured_states:
            assert state["strategy_type"] == "dfs"
            assert "stack" in state
            assert "dfs_seen" in state
            # Stack items should have depth
            for item in state["stack"]:
                assert "url" in item
                assert "parent_url" in item
                assert "depth" in item