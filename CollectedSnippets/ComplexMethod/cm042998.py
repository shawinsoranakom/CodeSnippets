async def test_verify_database_storage(self):
        """Verify all validation metadata is properly stored in database."""
        url = "https://docs.python.org/3/library/asyncio.html"

        browser_config = BrowserConfig(headless=True, verbose=False)
        config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED, check_cache_freshness=False)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url, config=config)

        assert result.success

        # Verify all fields in database
        metadata = await async_db_manager.aget_cache_metadata(url)

        assert metadata is not None, "Metadata must be stored"
        assert "url" in metadata
        assert "etag" in metadata
        assert "last_modified" in metadata
        assert "head_fingerprint" in metadata
        assert "cached_at" in metadata
        assert "response_headers" in metadata

        print(f"\nDatabase storage verification for {url}:")
        print(f"  - etag: {metadata['etag'][:40] if metadata['etag'] else 'None'}...")
        print(f"  - last_modified: {metadata['last_modified']}")
        print(f"  - head_fingerprint: {metadata['head_fingerprint']}")
        print(f"  - cached_at: {metadata['cached_at']}")
        print(f"  - response_headers keys: {list(metadata['response_headers'].keys())[:5]}...")

        # At least one validation field should be populated
        has_validation_data = (
            metadata["etag"] or
            metadata["last_modified"] or
            metadata["head_fingerprint"]
        )
        assert has_validation_data, "Should have at least one validation field"