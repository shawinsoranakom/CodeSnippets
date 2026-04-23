async def test_mix_of_success_and_failure(self):
        self.pipe.LOG_FAILED_RESULTS = False
        rsp1 = Response("http://url1")
        req1 = Request("http://url1", meta={"response": rsp1})
        exc = Exception("foo")
        req2 = Request("http://url2", meta={"response": exc})
        item = {"requests": [req1, req2]}
        new_item = await self.pipe.process_item(item)
        assert len(new_item["results"]) == 2
        assert new_item["results"][0] == (True, {})
        assert new_item["results"][1][0] is False
        assert isinstance(new_item["results"][1][1], Failure)
        assert new_item["results"][1][1].value == exc
        m = self.pipe._mockcalled
        # only once
        assert m[0] == "get_media_requests"  # first hook called
        assert m.count("get_media_requests") == 1
        assert m.count("item_completed") == 1
        assert m[-1] == "item_completed"  # last hook called
        # twice, one per request
        assert m.count("media_to_download") == 2
        # one to handle success and other for failure
        assert m.count("media_downloaded") == 1
        assert m.count("media_failed") == 1