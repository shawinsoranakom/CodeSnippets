def test_timeout_failure(self):
        crawler = get_crawler(DelaySpider, {"DOWNLOAD_TIMEOUT": 0.35})
        yield crawler.crawl(n=0.5, mockserver=self.mockserver)
        assert crawler.spider.t1 > 0
        assert crawler.spider.t2 == 0
        assert crawler.spider.t2_err > 0
        assert crawler.spider.t2_err > crawler.spider.t1

        # server hangs after receiving response headers
        crawler = get_crawler(DelaySpider, {"DOWNLOAD_TIMEOUT": 0.35})
        yield crawler.crawl(n=0.5, b=1, mockserver=self.mockserver)
        assert crawler.spider.t1 > 0
        assert crawler.spider.t2 == 0
        assert crawler.spider.t2_err > 0
        assert crawler.spider.t2_err > crawler.spider.t1