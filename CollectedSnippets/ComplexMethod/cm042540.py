def test_callback_kwargs(self):
        crawler = get_crawler(KeywordArgumentsSpider)
        with LogCapture() as log:
            yield crawler.crawl(mockserver=self.mockserver)
        assert all(crawler.spider.checks)
        assert len(crawler.spider.checks) == crawler.stats.get_value("boolean_checks")
        # check exceptions for argument mismatch
        exceptions = {}
        for line in log.records:
            for key in ("takes_less", "takes_more"):
                if key in line.getMessage():
                    exceptions[key] = line
        assert exceptions["takes_less"].exc_info[0] is TypeError
        assert str(exceptions["takes_less"].exc_info[1]).endswith(
            "parse_takes_less() got an unexpected keyword argument 'number'"
        ), "Exception message: " + str(exceptions["takes_less"].exc_info[1])
        assert exceptions["takes_more"].exc_info[0] is TypeError
        assert str(exceptions["takes_more"].exc_info[1]).endswith(
            "parse_takes_more() missing 1 required positional argument: 'other'"
        ), "Exception message: " + str(exceptions["takes_more"].exc_info[1])