def lr_rotation(node: MyNode) -> MyNode:
    left_child = node.get_left()
    assert left_child is not None
    node.set_left(left_rotation(left_child))
    return right_rotation(node)
