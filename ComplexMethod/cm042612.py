def test_middleware_works(self):
        crawler = get_crawler(_HttpErrorSpider)
        yield crawler.crawl(mockserver=self.mockserver)
        assert not crawler.spider.skipped
        assert crawler.spider.parsed == {"200"}
        assert crawler.spider.failed == {"404", "402", "500"}

        get_value = crawler.stats.get_value
        assert get_value("httperror/response_ignored_count") == 3
        assert get_value("httperror/response_ignored_status_count/404") == 1
        assert get_value("httperror/response_ignored_status_count/402") == 1
        assert get_value("httperror/response_ignored_status_count/500") == 1