def insert_node(head: Node | None, data: int) -> Node:
    new_node = Node(data)
    if head is None:
        return new_node

    temp_node = head
    while temp_node.next_node:
        temp_node = temp_node.next_node

    temp_node.next_node = new_node
    return head
