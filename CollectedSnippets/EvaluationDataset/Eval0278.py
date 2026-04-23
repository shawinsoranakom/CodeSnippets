def test_rotations() -> bool:
    tree = RedBlackTree(0)
    tree.left = RedBlackTree(-10, parent=tree)
    tree.right = RedBlackTree(10, parent=tree)
    tree.left.left = RedBlackTree(-20, parent=tree.left)
    tree.left.right = RedBlackTree(-5, parent=tree.left)
    tree.right.left = RedBlackTree(5, parent=tree.right)
    tree.right.right = RedBlackTree(20, parent=tree.right)
    left_rot = RedBlackTree(10)
    left_rot.left = RedBlackTree(0, parent=left_rot)
    left_rot.left.left = RedBlackTree(-10, parent=left_rot.left)
    left_rot.left.right = RedBlackTree(5, parent=left_rot.left)
    left_rot.left.left.left = RedBlackTree(-20, parent=left_rot.left.left)
    left_rot.left.left.right = RedBlackTree(-5, parent=left_rot.left.left)
    left_rot.right = RedBlackTree(20, parent=left_rot)
    tree = tree.rotate_left()
    if tree != left_rot:
        return False
    tree = tree.rotate_right()
    tree = tree.rotate_right()
    right_rot = RedBlackTree(-10)
    right_rot.left = RedBlackTree(-20, parent=right_rot)
    right_rot.right = RedBlackTree(0, parent=right_rot)
    right_rot.right.left = RedBlackTree(-5, parent=right_rot.right)
    right_rot.right.right = RedBlackTree(10, parent=right_rot.right)
    right_rot.right.right.left = RedBlackTree(5, parent=right_rot.right.right)
    right_rot.right.right.right = RedBlackTree(20, parent=right_rot.right.right)
    return tree == right_rot

