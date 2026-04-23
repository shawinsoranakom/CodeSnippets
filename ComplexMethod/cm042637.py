async def _test_delay(
        self, total: int, delay: float, randomize: bool = False
    ) -> None:
        crawl_kwargs = {
            "maxlatency": delay * 2,
            "mockserver": self.mockserver,
            "total": total,
        }
        tolerance = 1 - (0.6 if randomize else 0.2)

        settings = {"DOWNLOAD_DELAY": delay, "RANDOMIZE_DOWNLOAD_DELAY": randomize}
        crawler = get_crawler(FollowAllSpider, settings)
        await crawler.crawl_async(**crawl_kwargs)
        assert crawler.spider
        assert isinstance(crawler.spider, FollowAllSpider)
        times = crawler.spider.times
        total_time = times[-1] - times[0]
        average = total_time / (len(times) - 1)
        assert average > delay * tolerance, f"download delay too small: {average}"

        # Ensure that the same test parameters would cause a failure if no
        # download delay is set. Otherwise, it means we are using a combination
        # of ``total`` and ``delay`` values that are too small for the test
        # code above to have any meaning.
        settings["DOWNLOAD_DELAY"] = 0
        crawler = get_crawler(FollowAllSpider, settings)
        await crawler.crawl_async(**crawl_kwargs)
        assert crawler.spider
        assert isinstance(crawler.spider, FollowAllSpider)
        times = crawler.spider.times
        total_time = times[-1] - times[0]
        average = total_time / (len(times) - 1)
        assert average <= delay / tolerance, "test total or delay values are too small"