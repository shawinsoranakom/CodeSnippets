async def test_state_export_json_serializable(self):
        """Verify exported state can be JSON serialized."""
        captured_states: List[Dict] = []

        async def capture_state(state: Dict[str, Any]):
            # Verify JSON serializable
            json_str = json.dumps(state)
            parsed = json.loads(json_str)
            captured_states.append(parsed)

        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=10,
            on_state_change=capture_state,
        )

        # Create mock crawler that returns predictable results
        mock_crawler = create_mock_crawler_with_links(num_links=3)
        mock_config = create_mock_config()

        results = await strategy._arun_batch("https://example.com", mock_crawler, mock_config)

        # Verify states were captured
        assert len(captured_states) > 0

        # Verify state structure
        for state in captured_states:
            assert state["strategy_type"] == "bfs"
            assert "visited" in state
            assert "pending" in state
            assert "depths" in state
            assert "pages_crawled" in state
            assert isinstance(state["visited"], list)
            assert isinstance(state["pending"], list)
            assert isinstance(state["depths"], dict)
            assert isinstance(state["pages_crawled"], int)