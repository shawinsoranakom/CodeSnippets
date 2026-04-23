def test_logging(self):
        crawler = get_crawler(_HttpErrorSpider)
        with LogCapture() as log:
            yield crawler.crawl(mockserver=self.mockserver, bypass_status_codes={402})
        assert crawler.spider.parsed == {"200", "402"}
        assert crawler.spider.skipped == {"402"}
        assert crawler.spider.failed == {"404", "500"}

        assert "Ignoring response <404" in str(log)
        assert "Ignoring response <500" in str(log)
        assert "Ignoring response <200" not in str(log)
        assert "Ignoring response <402" not in str(log)