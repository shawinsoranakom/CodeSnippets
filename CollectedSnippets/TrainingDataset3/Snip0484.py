def make_linked_list(elements_list: list | tuple) -> Node:
    if not elements_list:
        raise ValueError("The Elements List is empty")

    head = Node(elements_list[0])
    current = head
    for data in elements_list[1:]:
        current.next = Node(data)
        current = current.next
    return head
