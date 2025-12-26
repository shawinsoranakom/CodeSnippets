def inorder(node: None | BinaryTreeNode) -> list[int]: 
    if node:
        inorder_array = inorder(node.left_child)
        inorder_array = [*inorder_array, node.data]
        inorder_array = inorder_array + inorder(node.right_child)
    else:
        inorder_array = []
    return inorder_array
