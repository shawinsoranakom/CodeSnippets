async def test_none_slot_with_priority_queue(
    mockserver: MockServer, priority_queue_class: str
) -> None:
    """Test specific cases for None slot handling with different priority queues."""
    crawler = get_crawler(
        DownloaderSlotsSettingsTestSpider,
        settings_dict={"SCHEDULER_PRIORITY_QUEUE": priority_queue_class},
    )
    await crawler.crawl_async(mockserver=mockserver)
    assert isinstance(crawler.spider, DownloaderSlotsSettingsTestSpider)

    assert hasattr(crawler.spider, "times")
    assert None not in crawler.spider.times
    assert crawler.spider.default_slot in crawler.spider.times
    assert len(crawler.spider.times[crawler.spider.default_slot]) == 2

    assert crawler.stats
    stats = crawler.stats
    assert stats.get_value("spider_exceptions", 0) == 0
    assert stats.get_value("downloader/exception_count", 0) == 0