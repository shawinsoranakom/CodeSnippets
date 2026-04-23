def test_queue_push_pop_one(self):
        temp_dir = tempfile.mkdtemp()
        queue = ScrapyPriorityQueue.from_crawler(
            self.crawler, FifoMemoryQueue, temp_dir
        )
        assert queue.pop() is None
        assert len(queue) == 0
        req1 = Request("https://example.org/1", priority=1)
        queue.push(req1)
        assert len(queue) == 1
        dequeued = queue.pop()
        assert len(queue) == 0
        assert dequeued.url == req1.url
        assert dequeued.priority == req1.priority
        assert not queue.close()