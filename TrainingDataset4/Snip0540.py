def dequeue(self) -> int:
    for queue in self.queues:
        if queue:
            return queue.pop(0)
    raise UnderFlowError("All queues are empty")
