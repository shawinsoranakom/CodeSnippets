def test_order(self, q: queuelib.queue.BaseQueue, test_peek: bool):
        if test_peek and not HAVE_PEEK:
            pytest.skip("The queuelib queues do not define peek")
        if not test_peek and HAVE_PEEK:
            pytest.skip("The queuelib queues define peek")
        assert len(q) == 0
        if test_peek:
            assert q.peek() is None
        assert q.pop() is None
        req1 = Request("http://www.example.com/1")
        req2 = Request("http://www.example.com/2")
        req3 = Request("http://www.example.com/3")
        q.push(req1)
        q.push(req2)
        q.push(req3)
        if not test_peek:
            with pytest.raises(
                NotImplementedError,
                match="The underlying queue class does not implement 'peek'",
            ):
                q.peek()
        reqs = [req1, req2, req3] if self.is_fifo else [req3, req2, req1]
        for i, req in enumerate(reqs):
            assert len(q) == 3 - i
            if test_peek:
                result = q.peek()
                assert result is not None
                assert result.url == req.url
            result = q.pop()
            assert result is not None
            assert result.url == req.url
        assert len(q) == 0
        if test_peek:
            assert q.peek() is None
        assert q.pop() is None
        q.close()