def dequeue(self) -> int:
    if not self.queue:
        raise UnderFlowError("The queue is empty")
    else:
        data = min(self.queue)
        self.queue.remove(data)
        return data
