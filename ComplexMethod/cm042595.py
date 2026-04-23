def test_one_retry(self):
        request = Request("https://example.com")
        spider = self.get_spider()
        with LogCapture() as log:
            new_request = get_retry_request(
                request,
                spider=spider,
                max_retry_times=1,
            )
        assert isinstance(new_request, Request)
        assert new_request != request
        assert new_request.dont_filter
        expected_retry_times = 1
        assert new_request.meta["retry_times"] == expected_retry_times
        assert new_request.priority == -1
        expected_reason = "unspecified"
        for stat in ("retry/count", f"retry/reason_count/{expected_reason}"):
            assert spider.crawler.stats.get_value(stat) == 1
        log.check_present(
            (
                "scrapy.downloadermiddlewares.retry",
                "DEBUG",
                f"Retrying {request} (failed {expected_retry_times} times): "
                f"{expected_reason}",
            )
        )