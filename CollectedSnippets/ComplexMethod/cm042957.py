async def _test():
            async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
                bm = crawler.crawler_strategy.browser_manager
                config = CrawlerRunConfig()

                htmls = [
                    f"raw:<html><body><p>Concurrent page {i}</p></body></html>"
                    for i in range(5)
                ]
                tasks = [crawler.arun(h, config=config) for h in htmls]
                results = await asyncio.gather(*tasks)
                for r in results:
                    assert r.success

                # All done — refcounts should be 0
                for sig, count in bm._context_refcounts.items():
                    assert count == 0, (
                        f"After concurrent crawls, refcount for {sig[:8]} = {count}"
                    )
                assert len(bm._page_to_sig) == 0