def test_format_engine_status(self):
        est = []

        def cb(response):
            est.append(format_engine_status(crawler.engine))

        crawler = get_crawler(SingleRequestSpider)
        yield crawler.crawl(
            seed=self.mockserver.url("/"), callback_func=cb, mockserver=self.mockserver
        )
        assert len(est) == 1, est
        est = est[0].split("\n")[2:-2]  # remove header & footer
        # convert to dict
        est = [x.split(":") for x in est]
        est = [x for sublist in est for x in sublist]  # flatten
        est = [x.lstrip().rstrip() for x in est]
        it = iter(est)
        s = dict(zip(it, it, strict=False))

        assert s["engine.spider.name"] == crawler.spider.name
        assert s["len(engine.scraper.slot.active)"] == "1"