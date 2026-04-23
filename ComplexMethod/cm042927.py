async def test_with_docker_client(filter_chain: list[URLFilter], max_pages: int = 20, timeout: int = 30) -> bool:
    """Test using the Docker client (same as 1419.py)."""
    from crawl4ai.docker_client import Crawl4aiDockerClient

    print("=" * 60)
    print("Testing with Docker Client")
    print("=" * 60)

    try:
        async with Crawl4aiDockerClient(
            base_url=BASE_URL,
            verbose=True,
        ) as client:

            crawler_config = CrawlerRunConfig(
                deep_crawl_strategy=BFSDeepCrawlStrategy(
                    max_depth=2,  # Keep it shallow for testing
                    max_pages=max_pages,  # Limit pages for testing
                    filter_chain=FilterChain(filter_chain)
                ),
                cache_mode=CacheMode.BYPASS,
            )

            print("\n1. Testing crawl with filters...")
            results = await client.crawl(
                ["https://docs.crawl4ai.com"],  # Simple test page
                browser_config=BrowserConfig(headless=True),
                crawler_config=crawler_config,
                hooks_timeout=timeout,
            )

            if results:
                print(f"✅ Crawl succeeded! Type: {type(results)}")
                if hasattr(results, 'success'):
                    print(f"✅ Results success: {results.success}")
                    # Test that we can iterate results without JSON errors
                    if hasattr(results, '__iter__'):
                        for i, result in enumerate(results):
                            if hasattr(result, 'url'):
                                print(f"   Result {i}: {result.url[:50]}...")
                            else:
                                print(f"   Result {i}: {str(result)[:50]}...")
                else:
                    # Handle list of results
                    print(f"✅ Got {len(results)} results")
                    for i, result in enumerate(results[:3]):  # Show first 3
                        print(f"   Result {i}: {result.url[:50]}...")
            else:
                print("❌ Crawl failed - no results returned")
                return False

        print("\n✅ Docker client test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Docker client test failed: {e}")
        traceback.print_exc()
        return False