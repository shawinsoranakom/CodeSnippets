def test_enqueue_dequeue(self):
        open_result = yield self.scheduler.open(Spider("foo"))
        assert open_result == "open"
        assert not self.scheduler.has_pending_requests()

        for url in URLS:
            assert self.scheduler.enqueue_request(Request(url))
            assert not self.scheduler.enqueue_request(Request(url))

        assert self.scheduler.has_pending_requests()
        assert len(self.scheduler) == len(URLS)

        dequeued = []
        while self.scheduler.has_pending_requests():
            request = self.scheduler.next_request()
            dequeued.append(request.url)
        assert set(dequeued) == set(URLS)

        assert not self.scheduler.has_pending_requests()
        assert len(self.scheduler) == 0

        close_result = yield self.scheduler.close("")
        assert close_result == "close"