def test_processed_request(crawler: Crawler) -> None:
    class ProcessReqSpiderMiddleware(BaseSpiderMiddleware):
        def get_processed_request(
            self, request: Request, response: Response | None
        ) -> Request | None:
            if request.url == "data:2,":
                return None
            if request.url == "data:3,":
                return Request("data:30,")
            return request

    mw = ProcessReqSpiderMiddleware.from_crawler(crawler)
    test_req1 = Request("data:1,")
    test_req2 = Request("data:2,")
    test_req3 = Request("data:3,")
    spider_output = [test_req1, {"foo": "bar"}, test_req2, test_req3]
    for processed in [
        list(mw.process_spider_output(Response("data:,"), spider_output)),
        list(mw.process_start_requests(spider_output, None)),  # type: ignore[arg-type]
    ]:
        assert len(processed) == 3
        assert isinstance(processed[0], Request)
        assert processed[0].url == "data:1,"
        assert processed[1] == {"foo": "bar"}
        assert isinstance(processed[2], Request)
        assert processed[2].url == "data:30,"