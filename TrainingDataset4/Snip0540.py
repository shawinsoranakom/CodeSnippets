def dequeue(self) -> int:
    for queue in self.queues:
        if queue:
            return queue.pop(0)
    raise UnderFlowError("All queues are empty")

def __str__(self) -> str:
    return "\n".join(f"Priority {i}: {q}" for i, q in enumerate(self.queues))
