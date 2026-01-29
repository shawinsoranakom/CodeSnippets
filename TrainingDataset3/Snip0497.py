def print_linked_list(head: Node | None) -> None:
    if head is None:
        return
    while head.next_node is not None:
        print(head.data, end="->")
        head = head.next_node
    print(head.data)
