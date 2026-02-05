def __init__(self, data: T):
    self.data = data
    self.next: Node[T] | None = None
