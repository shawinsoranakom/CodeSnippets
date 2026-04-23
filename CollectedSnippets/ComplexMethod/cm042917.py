async def test_state_export_includes_scored_queue(self):
        """Verify Best-First state includes queue with scores."""
        captured_states: List[Dict] = []

        async def capture_state(state: Dict[str, Any]):
            captured_states.append(state)

        scorer = KeywordRelevanceScorer(keywords=["important"], weight=1.0)

        strategy = BestFirstCrawlingStrategy(
            max_depth=2,
            max_pages=10,
            url_scorer=scorer,
            on_state_change=capture_state,
        )

        mock_crawler = create_mock_crawler_with_links(num_links=3, include_keyword=True)
        mock_config = create_mock_config(stream=True)

        async for _ in strategy._arun_stream("https://example.com", mock_crawler, mock_config):
            pass

        assert len(captured_states) > 0

        for state in captured_states:
            assert state["strategy_type"] == "best_first"
            assert "queue_items" in state
            for item in state["queue_items"]:
                assert "score" in item
                assert "depth" in item
                assert "url" in item
                assert "parent_url" in item