def test_insert_delete() -> bool:
    tree = RedBlackTree(0)
    tree = tree.insert(-12)
    tree = tree.insert(8)
    tree = tree.insert(-8)
    tree = tree.insert(15)
    tree = tree.insert(4)
    tree = tree.insert(12)
    tree = tree.insert(10)
    tree = tree.insert(9)
    tree = tree.insert(11)
    tree = tree.remove(15)
    tree = tree.remove(-12)
    tree = tree.remove(9)
    if not tree.check_color_properties():
        return False
    return list(tree.inorder_traverse()) == [-8, 0, 4, 8, 10, 11, 12]
