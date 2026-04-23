def test_enqueue_dequeue(self):
        assert not self.scheduler.has_pending_requests()
        for url in URLS:
            assert self.scheduler.enqueue_request(Request(url))
            assert not self.scheduler.enqueue_request(Request(url))
        assert self.scheduler.has_pending_requests

        dequeued = []
        while self.scheduler.has_pending_requests():
            request = self.scheduler.next_request()
            dequeued.append(request.url)
        assert set(dequeued) == set(URLS)
        assert not self.scheduler.has_pending_requests()