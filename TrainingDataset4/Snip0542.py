def enqueue(self, data: int) -> None:
    if len(self.queue) == 100:
        raise OverFlowError("Maximum queue size is 100")
    self.queue.append(data)
