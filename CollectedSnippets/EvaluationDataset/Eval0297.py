def make_asymmetric_tree() -> Node:
    root = Node(1)
    root.left = Node(2)
    root.right = Node(2)
    root.left.left = Node(3)
    root.left.right = Node(4)
    root.right.left = Node(3)
    root.right.right = Node(4)
    return root

