def test_insertion_speed() -> bool:
    tree = RedBlackTree(-1)
    for i in range(300000):
        tree = tree.insert(i)
    return True
