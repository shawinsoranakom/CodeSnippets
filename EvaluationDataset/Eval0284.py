def test_min_max() -> bool:
    tree = RedBlackTree(0)
    tree.insert(-16)
    tree.insert(16)
    tree.insert(8)
    tree.insert(24)
    tree.insert(20)
    tree.insert(22)
    return not (tree.get_max() != 22 or tree.get_min() != -16)
