def test_two_retries(self):
        spider = self.get_spider()
        request = Request("https://example.com")
        new_request = request
        max_retry_times = 2
        for index in range(max_retry_times):
            with LogCapture() as log:
                new_request = get_retry_request(
                    new_request,
                    spider=spider,
                    max_retry_times=max_retry_times,
                )
            assert isinstance(new_request, Request)
            assert new_request != request
            assert new_request.dont_filter
            expected_retry_times = index + 1
            assert new_request.meta["retry_times"] == expected_retry_times
            assert new_request.priority == -expected_retry_times
            expected_reason = "unspecified"
            for stat in ("retry/count", f"retry/reason_count/{expected_reason}"):
                value = spider.crawler.stats.get_value(stat)
                assert value == expected_retry_times
            log.check_present(
                (
                    "scrapy.downloadermiddlewares.retry",
                    "DEBUG",
                    f"Retrying {request} (failed {expected_retry_times} times): "
                    f"{expected_reason}",
                )
            )

        with LogCapture() as log:
            new_request = get_retry_request(
                new_request,
                spider=spider,
                max_retry_times=max_retry_times,
            )
        assert new_request is None
        assert spider.crawler.stats.get_value("retry/max_reached") == 1
        failure_count = max_retry_times + 1
        expected_reason = "unspecified"
        log.check_present(
            (
                "scrapy.downloadermiddlewares.retry",
                "ERROR",
                f"Gave up retrying {request} (failed {failure_count} times): "
                f"{expected_reason}",
            )
        )