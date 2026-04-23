class LinkedList:
    def __init__(self):
        self.head = None

    def push(self, new_data: int) -> int:
        new_node = Node(new_data)
        new_node.next = self.head
        self.head = new_node
        return self.head.data

    def middle_element(self) -> int | None:
        slow_pointer = self.head
        fast_pointer = self.head
        if self.head:
            while fast_pointer and fast_pointer.next:
                fast_pointer = fast_pointer.next.next
                slow_pointer = slow_pointer.next
            return slow_pointer.data
        else:
            print("No element found.")
            return None
