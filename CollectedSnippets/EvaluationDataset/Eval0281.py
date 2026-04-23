def test_insert_and_search() -> bool:
    tree = RedBlackTree(0)
    tree.insert(8)
    tree.insert(-8)
    tree.insert(4)
    tree.insert(12)
    tree.insert(10)
    tree.insert(11)
    if any(i in tree for i in (5, -6, -10, 13)):
        return False
    return all(i in tree for i in (11, 12, -8, 0))
