class CircularQueueLinkedList:

    def __init__(self, initial_capacity: int = 6) -> None:
        self.front: Node | None = None
        self.rear: Node | None = None
        self.create_linked_list(initial_capacity)

    def create_linked_list(self, initial_capacity: int) -> None:
        current_node = Node()
        self.front = current_node
        self.rear = current_node
        previous_node = current_node
        for _ in range(1, initial_capacity):
            current_node = Node()
            previous_node.next = current_node
            current_node.prev = previous_node
            previous_node = current_node
        previous_node.next = self.front
        self.front.prev = previous_node

    def is_empty(self) -> bool:

        return (
            self.front == self.rear
            and self.front is not None
            and self.front.data is None
        )

    def first(self) -> Any | None:
        self.check_can_perform_operation()
        return self.front.data if self.front else None

    def enqueue(self, data: Any) -> None:
        if self.rear is None:
            return

        self.check_is_full()
        if not self.is_empty():
            self.rear = self.rear.next
        if self.rear:
            self.rear.data = data

    def dequeue(self) -> Any:
        self.check_can_perform_operation()
        if self.rear is None or self.front is None:
            return None
        if self.front == self.rear:
            data = self.front.data
            self.front.data = None
            return data

        old_front = self.front
        self.front = old_front.next
        data = old_front.data
        old_front.data = None
        return data

    def check_can_perform_operation(self) -> None:
        if self.is_empty():
            raise Exception("Empty Queue")

    def check_is_full(self) -> None:
        if self.rear and self.rear.next == self.front:
            raise Exception("Full Queue")
