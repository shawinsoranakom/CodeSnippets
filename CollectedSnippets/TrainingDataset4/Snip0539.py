def enqueue(self, priority: int, data: int) -> None:
    try:
        if len(self.queues[priority]) >= 100:
            raise OverflowError("Maximum queue size is 100")
        self.queues[priority].append(data)
    except IndexError:
        raise ValueError("Valid priorities are 0, 1, and 2")
