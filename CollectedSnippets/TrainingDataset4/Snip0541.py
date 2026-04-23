def __str__(self) -> str:
    return "\n".join(f"Priority {i}: {q}" for i, q in enumerate(self.queues))
