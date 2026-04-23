def test_processed_both(crawler: Crawler) -> None:
    class ProcessBothSpiderMiddleware(BaseSpiderMiddleware):
        def get_processed_request(
            self, request: Request, response: Response | None
        ) -> Request | None:
            if request.url == "data:2,":
                return None
            if request.url == "data:3,":
                return Request("data:30,")
            return request

        def get_processed_item(self, item: Any, response: Response | None) -> Any:
            if item["foo"] == 2:
                return None
            if item["foo"] == 3:
                item["foo"] = 30
            return item

    mw = ProcessBothSpiderMiddleware.from_crawler(crawler)
    test_req1 = Request("data:1,")
    test_req2 = Request("data:2,")
    test_req3 = Request("data:3,")
    spider_output = [
        test_req1,
        {"foo": 1},
        {"foo": 2},
        test_req2,
        {"foo": 3},
        test_req3,
    ]
    for processed in [
        list(mw.process_spider_output(Response("data:,"), spider_output)),
        list(mw.process_start_requests(spider_output, None)),  # type: ignore[arg-type]
    ]:
        assert len(processed) == 4
        assert isinstance(processed[0], Request)
        assert processed[0].url == "data:1,"
        assert processed[1] == {"foo": 1}
        assert processed[2] == {"foo": 30}
        assert isinstance(processed[3], Request)
        assert processed[3].url == "data:30,"