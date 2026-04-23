async def test_bytes_received_stop_download_errback(
        self, mockserver: MockServer
    ) -> None:
        # copy of TestCrawl.test_bytes_received_stop_download_errback()
        crawler = get_crawler(BytesReceivedErrbackSpider, self.settings_dict)
        await crawler.crawl_async(mockserver=mockserver, is_secure=self.is_secure)
        assert isinstance(crawler.spider, BytesReceivedErrbackSpider)
        assert crawler.spider.meta.get("response") is None
        assert isinstance(crawler.spider.meta["failure"], Failure)
        assert isinstance(crawler.spider.meta["failure"].value, StopDownload)
        assert isinstance(crawler.spider.meta["failure"].value.response, Response)
        assert crawler.spider.meta[
            "failure"
        ].value.response.body == crawler.spider.meta.get("bytes_received")
        assert (
            len(crawler.spider.meta["failure"].value.response.body)
            < crawler.spider.full_response_length
        )