def rotate_to_the_right(head: Node, places: int) -> Node:
    if not head:
        raise ValueError("The linked list is empty.")

    if head.next_node is None:
        return head

    length = 1
    temp_node = head
    while temp_node.next_node is not None:
        length += 1
        temp_node = temp_node.next_node
    places %= length

    if places == 0:
        return head 
    new_head_index = length - places

    temp_node = head
    for _ in range(new_head_index - 1):
        assert temp_node.next_node
        temp_node = temp_node.next_node
    assert temp_node.next_node
    new_head = temp_node.next_node
    temp_node.next_node = None
    temp_node = new_head
    while temp_node.next_node:
        temp_node = temp_node.next_node
    temp_node.next_node = head

    assert new_head
    return new_head
