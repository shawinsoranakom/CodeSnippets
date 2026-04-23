def test_push_pop(self):
        assert len(self.queue) == 0
        assert self.queue.pop() is None
        req1 = Request("http://www.example.com/1")
        req2 = Request("http://www.example.com/2")
        req3 = Request("http://www.example.com/3")
        self.queue.push(req1)
        self.queue.push(req2)
        self.queue.push(req3)
        assert len(self.queue) == 3
        assert self.queue.pop().url == req1.url
        assert len(self.queue) == 2
        assert self.queue.pop().url == req2.url
        assert len(self.queue) == 1
        assert self.queue.pop().url == req3.url
        assert len(self.queue) == 0
        assert self.queue.pop() is None