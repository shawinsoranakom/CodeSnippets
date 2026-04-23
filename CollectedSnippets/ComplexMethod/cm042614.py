def test_logging_level(self):
        # HttpError logs ignored responses with level INFO
        crawler = get_crawler(_HttpErrorSpider)
        with LogCapture(level=logging.INFO) as log:
            yield crawler.crawl(mockserver=self.mockserver)
        assert crawler.spider.parsed == {"200"}
        assert crawler.spider.failed == {"404", "402", "500"}

        assert "Ignoring response <402" in str(log)
        assert "Ignoring response <404" in str(log)
        assert "Ignoring response <500" in str(log)
        assert "Ignoring response <200" not in str(log)

        # with level WARNING, we shouldn't capture anything from HttpError
        crawler = get_crawler(_HttpErrorSpider)
        with LogCapture(level=logging.WARNING) as log:
            yield crawler.crawl(mockserver=self.mockserver)
        assert crawler.spider.parsed == {"200"}
        assert crawler.spider.failed == {"404", "402", "500"}

        assert "Ignoring response <402" not in str(log)
        assert "Ignoring response <404" not in str(log)
        assert "Ignoring response <500" not in str(log)
        assert "Ignoring response <200" not in str(log)