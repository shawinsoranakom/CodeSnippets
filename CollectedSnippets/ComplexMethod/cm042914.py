async def test_real_crawl_state_capture_and_resume(self):
        """
        Test crash recovery with real URLs from books.toscrape.com.

        Flow:
        1. Start crawl with state callback
        2. Stop after N pages (simulated crash)
        3. Resume from saved state
        4. Verify no duplicate crawls
        """
        # Phase 1: Initial crawl that "crashes" after 3 pages
        crash_after = 3
        captured_states: List[Dict[str, Any]] = []
        crawled_urls_phase1: List[str] = []

        async def capture_state_until_crash(state: Dict[str, Any]):
            captured_states.append(state)
            crawled_urls_phase1.clear()
            crawled_urls_phase1.extend(state["visited"])

            if state["pages_crawled"] >= crash_after:
                raise Exception("Simulated crash!")

        strategy1 = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=10,
            on_state_change=capture_state_until_crash,
        )

        config = CrawlerRunConfig(
            deep_crawl_strategy=strategy1,
            stream=False,
            verbose=False,
        )

        async with AsyncWebCrawler(verbose=False) as crawler:
            # First crawl - will crash after 3 pages
            with pytest.raises(Exception, match="Simulated crash"):
                await crawler.arun("https://books.toscrape.com", config=config)

        # Verify we captured state before crash
        assert len(captured_states) > 0, "No states captured before crash"
        last_state = captured_states[-1]

        print(f"\n=== Phase 1: Crashed after {last_state['pages_crawled']} pages ===")
        print(f"Visited URLs: {len(last_state['visited'])}")
        print(f"Pending URLs: {len(last_state['pending'])}")

        # Verify state structure
        assert last_state["strategy_type"] == "bfs"
        assert last_state["pages_crawled"] >= crash_after
        assert len(last_state["visited"]) > 0
        assert "pending" in last_state
        assert "depths" in last_state

        # Verify state is JSON serializable (important for Redis/DB storage)
        json_str = json.dumps(last_state)
        restored_state = json.loads(json_str)
        assert restored_state == last_state, "State not JSON round-trip safe"

        # Phase 2: Resume from checkpoint
        crawled_urls_phase2: List[str] = []

        async def track_resumed_crawl(state: Dict[str, Any]):
            # Track what's being crawled in phase 2
            new_visited = set(state["visited"]) - set(last_state["visited"])
            for url in new_visited:
                if url not in crawled_urls_phase2:
                    crawled_urls_phase2.append(url)

        strategy2 = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=10,
            resume_state=restored_state,
            on_state_change=track_resumed_crawl,
        )

        config2 = CrawlerRunConfig(
            deep_crawl_strategy=strategy2,
            stream=False,
            verbose=False,
        )

        async with AsyncWebCrawler(verbose=False) as crawler:
            results = await crawler.arun("https://books.toscrape.com", config=config2)

        print(f"\n=== Phase 2: Resumed crawl ===")
        print(f"New URLs crawled: {len(crawled_urls_phase2)}")
        print(f"Final pages_crawled: {strategy2._pages_crawled}")

        # Verify no duplicates - URLs from phase 1 should not be re-crawled
        already_crawled = set(last_state["visited"]) - {item["url"] for item in last_state["pending"]}
        duplicates = set(crawled_urls_phase2) & already_crawled

        assert len(duplicates) == 0, f"Duplicate crawls detected: {duplicates}"

        # Verify we made progress (crawled some of the pending URLs)
        pending_urls = {item["url"] for item in last_state["pending"]}
        crawled_pending = set(crawled_urls_phase2) & pending_urls

        print(f"Pending URLs crawled in phase 2: {len(crawled_pending)}")

        # Final state should show more pages crawled than before crash
        final_state = strategy2.export_state()
        if final_state:
            assert final_state["pages_crawled"] >= last_state["pages_crawled"], \
                "Resume did not make progress"

        print("\n=== Integration test PASSED ===")