def test_peek(self):
        if not hasattr(queuelib.queue.FifoMemoryQueue, "peek"):
            pytest.skip("queuelib.queue.FifoMemoryQueue.peek is undefined")
        temp_dir = tempfile.mkdtemp()
        queue = ScrapyPriorityQueue.from_crawler(
            self.crawler, FifoMemoryQueue, temp_dir
        )
        assert len(queue) == 0
        assert queue.peek() is None
        req1 = Request("https://example.org/1")
        req2 = Request("https://example.org/2")
        req3 = Request("https://example.org/3")
        queue.push(req1)
        queue.push(req2)
        queue.push(req3)
        assert len(queue) == 3
        assert queue.peek().url == req1.url
        assert queue.pop().url == req1.url
        assert len(queue) == 2
        assert queue.peek().url == req2.url
        assert queue.pop().url == req2.url
        assert len(queue) == 1
        assert queue.peek().url == req3.url
        assert queue.pop().url == req3.url
        assert not queue.close()