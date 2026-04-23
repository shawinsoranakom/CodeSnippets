def test_one_element(self, q: queuelib.queue.BaseQueue, test_peek: bool):
        if test_peek and not HAVE_PEEK:
            pytest.skip("The queuelib queues do not define peek")
        if not test_peek and HAVE_PEEK:
            pytest.skip("The queuelib queues define peek")
        assert len(q) == 0
        if test_peek:
            assert q.peek() is None
        assert q.pop() is None
        req = Request("http://www.example.com")
        q.push(req)
        assert len(q) == 1
        if test_peek:
            result = q.peek()
            assert result is not None
            assert result.url == req.url
        else:
            with pytest.raises(
                NotImplementedError,
                match="The underlying queue class does not implement 'peek'",
            ):
                q.peek()
        result = q.pop()
        assert result is not None
        assert result.url == req.url
        assert len(q) == 0
        if test_peek:
            assert q.peek() is None
        assert q.pop() is None
        q.close()