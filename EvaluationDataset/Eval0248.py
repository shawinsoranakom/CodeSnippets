def insert(node: BinaryTreeNode | None, new_value: int) -> BinaryTreeNode | None:
    if node is None:
        node = BinaryTreeNode(new_value)
        return node

    if new_value < node.data:
        node.left_child = insert(node.left_child, new_value)
    else:
        node.right_child = insert(node.right_child, new_value)
    return node
