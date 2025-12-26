def test_tree_chaining() -> bool:
    tree = RedBlackTree(0)
    tree = tree.insert(-16).insert(16).insert(8).insert(24).insert(20).insert(22)
    if list(tree.inorder_traverse()) != [-16, 0, 8, 16, 20, 22, 24]:
        return False
    if list(tree.preorder_traverse()) != [0, -16, 16, 8, 22, 20, 24]:
        return False
    return list(tree.postorder_traverse()) == [-16, 8, 20, 24, 22, 16, 0]

