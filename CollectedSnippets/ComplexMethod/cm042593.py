def test_503(self):
        req = Request("http://www.scrapytest.org/503")
        rsp = Response("http://www.scrapytest.org/503", body=b"", status=503)

        # first retry
        req = self.mw.process_response(req, rsp)
        assert isinstance(req, Request)
        assert req.meta["retry_times"] == 1

        # second retry
        req = self.mw.process_response(req, rsp)
        assert isinstance(req, Request)
        assert req.meta["retry_times"] == 2

        # discard it
        assert self.mw.process_response(req, rsp) is rsp

        assert self.crawler.stats.get_value("retry/max_reached") == 1
        assert (
            self.crawler.stats.get_value("retry/reason_count/503 Service Unavailable")
            == 2
        )
        assert self.crawler.stats.get_value("retry/count") == 2