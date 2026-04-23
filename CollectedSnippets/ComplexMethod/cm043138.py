async def test_crash_recovery_json_serializable():
    """
    Verify the state dictionary can be serialized to JSON (for Redis/DB storage).

    NEW in v0.8.0: State dictionary is designed to be JSON-serializable
    for easy storage in Redis, databases, or files.
    """
    print_test("Crash Recovery - JSON Serializable", "State Structure")

    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

        captured_state: Optional[Dict] = None

        async def capture_state(state: Dict[str, Any]):
            nonlocal captured_state
            captured_state = state

        strategy = BFSDeepCrawlStrategy(
            max_depth=1,
            max_pages=2,
            on_state_change=capture_state,
        )

        config = CrawlerRunConfig(
            deep_crawl_strategy=strategy,
            verbose=False,
        )

        async with AsyncWebCrawler(verbose=False) as crawler:
            await crawler.arun("https://books.toscrape.com", config=config)

        if not captured_state:
            record_result("JSON Serializable", "State Structure", False,
                         "No state captured")
            return

        # Test JSON serialization round-trip
        try:
            json_str = json.dumps(captured_state)
            restored = json.loads(json_str)
        except (TypeError, json.JSONDecodeError) as e:
            record_result("JSON Serializable", "State Structure", False,
                         f"JSON serialization failed: {e}")
            return

        # Verify state structure
        required_fields = ["strategy_type", "visited", "pending", "depths", "pages_crawled"]
        missing = [f for f in required_fields if f not in restored]
        if missing:
            record_result("JSON Serializable", "State Structure", False,
                         f"Missing fields: {missing}")
            return

        # Verify types
        if not isinstance(restored["visited"], list):
            record_result("JSON Serializable", "State Structure", False,
                         "visited is not a list")
            return

        if not isinstance(restored["pages_crawled"], int):
            record_result("JSON Serializable", "State Structure", False,
                         "pages_crawled is not an int")
            return

        record_result("JSON Serializable", "State Structure", True,
                     f"State serializes to {len(json_str)} bytes, all fields present")

    except Exception as e:
        record_result("JSON Serializable", "State Structure", False, f"Exception: {e}")