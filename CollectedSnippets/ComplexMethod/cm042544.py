async def _test_request_order(
        self,
        start_nums,
        cb_nums=None,
        settings=None,
        response_seconds=None,
        download_slots=1,
        start_fn=None,
        parse_fn=None,
    ):
        cb_nums = cb_nums or []
        settings = settings or {}
        response_seconds = response_seconds or self.seconds

        cb_requests = deque(
            [self.request(num, response_seconds, download_slots) for num in cb_nums]
        )

        if start_fn is None:

            async def start_fn(spider):
                for num in start_nums:
                    yield self.request(num, response_seconds, download_slots)

        if parse_fn is None:

            def parse_fn(spider, response):
                while cb_requests:
                    yield cb_requests.popleft()

        class TestSpider(Spider):
            name = "test"
            start = start_fn
            parse = parse_fn

        actual_nums = []

        def track_num(request, spider):
            actual_nums.append(self.get_num(request))

        crawler = get_crawler(TestSpider, settings_dict=settings)
        crawler.signals.connect(track_num, signals.request_reached_downloader)
        await crawler.crawl_async()
        assert crawler.stats.get_value("finish_reason") == "finished"
        expected_nums = sorted(start_nums + cb_nums)
        assert actual_nums == expected_nums, f"{actual_nums=} != {expected_nums=}"